from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone
from pydantic import TypeAdapter, ValidationError

from recommendation.contracts import (
    RecommendationDraft,
)
from recommendation.contracts import (
    RecommendationOperation as RecommendationOperationContract,
)
from recommendation.models import Recommendation, RecommendationOperation
from training.models import Exercise, Workout, WorkoutExercise


class RecommendationNotFound(ValueError):
    pass


class RecommendationConflict(ValueError):
    pass


class RecommendationValidationError(ValueError):
    pass


@transaction.atomic
def create_recommendation(
    *,
    user: Any,
    conversation: Any,
    draft: RecommendationDraft | dict[str, Any],
    coach_message: Any = None,
    source: str = RecommendationOperation.Source.COACH_CHAT,
) -> Recommendation:
    """Validate and persist a recommendation ledger for one user and conversation.

    Creates the parent and all operation rows atomically, marking explicitly
    superseded operations resolved after confirming that they belong to the user.
    """
    draft = RecommendationDraft.model_validate(draft)
    recommendation = Recommendation.objects.create(
        user=user,
        conversation=conversation,
        coach_message=coach_message,
        summary=draft.summary,
        reason=draft.reason,
    )
    for item in draft.operations:
        supersedes = None
        if item.supersedes_operation_id:
            try:
                supersedes = RecommendationOperation.objects.get(
                    pk=item.supersedes_operation_id, recommendation__user=user
                )
            except RecommendationOperation.DoesNotExist as exc:
                raise RecommendationValidationError(
                    "Superseded operation was not found."
                ) from exc
        RecommendationOperation.objects.create(
            recommendation=recommendation,
            operation_type=item.operation_type,
            reason=item.reason,
            payload=item.payload.model_dump(mode="json"),
            source=source,
            created_by_message=coach_message,
            supersedes=supersedes,
        )
        if supersedes:
            supersedes.status = RecommendationOperation.Status.SUPERSEDED
            supersedes.resolved_at = timezone.now()
            supersedes.save(update_fields=["status", "resolved_at", "updated_at"])
    return recommendation


def get_recommendation(user: Any, recommendation_id: str) -> Recommendation | None:
    """Return one user-owned recommendation with its operations, or ``None``."""
    return (
        Recommendation.objects.filter(pk=recommendation_id, user=user)
        .prefetch_related("operations")
        .first()
    )


def serialize_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    """Project persisted operations into the public recommendation response shape.

    Superseded rows are hidden and temporary-workout exercise additions are nested
    below their corresponding add-workout operation.
    """
    operations = list(
        recommendation.operations.exclude(
            status=RecommendationOperation.Status.SUPERSEDED
        ).order_by("created_at")
    )
    children_by_temp: dict[str, list[dict[str, Any]]] = {}
    result: list[dict[str, Any]] = []
    for operation in operations:
        data = _serialize_operation(operation)
        temp_workout_id = (
            data["payload"].get("temporary_workout_id")
            if operation.operation_type == "add_exercise"
            else None
        )
        if temp_workout_id:
            children_by_temp.setdefault(str(temp_workout_id), []).append(data)
        else:
            result.append(data)
    for operation in result:
        if operation["operation_type"] == "add_workout":
            operation["exercise_operations"] = children_by_temp.pop(
                str(operation["payload"]["temporary_id"]), []
            )
    return {
        "id": str(recommendation.id),
        "summary": recommendation.summary,
        "reason": recommendation.reason,
        "operations": result,
    }


def _serialize_operation(operation: RecommendationOperation) -> dict[str, Any]:
    """Serialize one ledger row and convert stored zero-based positions for the API."""
    payload = dict(operation.payload)
    if operation.operation_type == "add_exercise" and "position" in payload:
        payload["position"] += 1
    if (
        operation.operation_type == "update_exercise"
        and payload.get("position") is not None
    ):
        payload["position"] += 1
    return {
        "id": str(operation.id),
        "status": operation.status,
        "operation_type": operation.operation_type,
        "display_text": operation.display_text,
        "reason": operation.reason,
        "payload": payload,
    }


_operation_adapter = TypeAdapter(RecommendationOperationContract)


@transaction.atomic
def revise_operation(
    *,
    user: Any,
    recommendation_id: str,
    operation_id: str,
    replacement: RecommendationOperationContract | dict[str, Any],
) -> Recommendation:
    """Replace a pending operation with a validated revision in the same target scope.

    The previous row remains in the ledger as ``superseded`` and the new row is
    returned through the parent recommendation projection.
    """
    operation = _operation(user, recommendation_id, operation_id)
    if operation.status != RecommendationOperation.Status.PENDING:
        raise RecommendationConflict("Only pending operations can be revised.")
    try:
        validated_replacement: RecommendationOperationContract = (
            _operation_adapter.validate_python(replacement)
        )
    except ValidationError as exc:
        raise RecommendationValidationError(str(exc)) from exc
    if validated_replacement.operation_type != operation.operation_type:
        raise RecommendationValidationError("A revision must keep the operation type.")
    _validate_revision_target(operation, validated_replacement)
    operation.status = RecommendationOperation.Status.SUPERSEDED
    operation.resolved_at = timezone.now()
    operation.updated_by = "user"
    operation.save(update_fields=["status", "resolved_at", "updated_by", "updated_at"])
    RecommendationOperation.objects.create(
        recommendation=operation.recommendation,
        operation_type=validated_replacement.operation_type,
        reason=validated_replacement.reason,
        payload=validated_replacement.payload.model_dump(mode="json"),
        source=operation.source,
        supersedes=operation,
        updated_by="user",
    )
    return operation.recommendation


def _validate_revision_target(
    operation: RecommendationOperation,
    replacement: RecommendationOperationContract,
) -> None:
    """Keep a revision attached to the same training target or temporary group."""
    original = operation.payload
    revised = replacement.payload.model_dump(mode="json")
    target_keys = {
        "add_workout": ("temporary_id",),
        "update_workout": ("workout_id",),
        "remove_workout": ("workout_id",),
        "add_exercise": ("workout_id", "temporary_workout_id", "temporary_id"),
        "update_exercise": ("workout_exercise_id",),
        "remove_exercise": ("workout_exercise_id",),
    }[operation.operation_type]
    if any(str(original.get(key)) != str(revised.get(key)) for key in target_keys):
        raise RecommendationValidationError(
            "A revision must keep the same recommendation target."
        )


def _operation(
    user: Any, recommendation_id: str, operation_id: str
) -> RecommendationOperation:
    """Fetch an operation only when it belongs to the requested recommendation and user."""
    try:
        return RecommendationOperation.objects.select_related("recommendation").get(
            pk=operation_id,
            recommendation_id=recommendation_id,
            recommendation__user=user,
        )
    except RecommendationOperation.DoesNotExist as exc:
        raise RecommendationNotFound("Recommendation operation was not found.") from exc


@transaction.atomic
def reject_operation(
    *, user: Any, recommendation_id: str, operation_id: str
) -> Recommendation:
    """Reject one pending operation without changing other recommendation operations."""
    operation = _operation(user, recommendation_id, operation_id)
    if operation.status != RecommendationOperation.Status.PENDING:
        raise RecommendationConflict("Operation is no longer pending.")
    operation.status = RecommendationOperation.Status.REJECTED
    operation.resolved_at = timezone.now()
    operation.updated_by = "user"
    operation.save(update_fields=["status", "resolved_at", "updated_by", "updated_at"])
    return operation.recommendation


@transaction.atomic
def reject_recommendation(*, user: Any, recommendation_id: str) -> Recommendation:
    """Reject every pending operation in a user-owned recommendation batch."""
    recommendation = get_recommendation(user, recommendation_id)
    if not recommendation:
        raise RecommendationNotFound("Recommendation was not found.")
    RecommendationOperation.objects.filter(
        recommendation=recommendation, status=RecommendationOperation.Status.PENDING
    ).update(
        status=RecommendationOperation.Status.REJECTED,
        resolved_at=timezone.now(),
        updated_by="user",
    )
    return recommendation


@transaction.atomic
def accept_operation(
    *, user: Any, recommendation_id: str, operation_id: str
) -> Recommendation:
    """Apply one pending operation, including dependent child exercises when required."""
    operation = _operation(user, recommendation_id, operation_id)
    if operation.status != RecommendationOperation.Status.PENDING:
        raise RecommendationConflict("Operation is no longer pending.")
    _apply_operations(user=user, operations=_operation_bundle(operation))
    return operation.recommendation


@transaction.atomic
def accept_recommendation(*, user: Any, recommendation_id: str) -> Recommendation:
    """Atomically apply every pending operation in a user-owned recommendation."""
    recommendation = get_recommendation(user, recommendation_id)
    if not recommendation:
        raise RecommendationNotFound("Recommendation was not found.")
    pending = list(
        recommendation.operations.filter(status=RecommendationOperation.Status.PENDING)
        .annotate(
            application_order=Case(
                When(
                    operation_type=RecommendationOperation.OperationType.ADD_WORKOUT,
                    then=Value(0),
                ),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("application_order", "created_at")
    )
    _apply_operations(user=user, operations=pending)
    return recommendation


def _operation_bundle(
    operation: RecommendationOperation,
) -> list[RecommendationOperation]:
    """Return the operation set that must be accepted together.

    Add-workout operations include their pending temporary-workout exercises;
    those children cannot be accepted independently.
    """
    if operation.operation_type != "add_workout":
        if operation.operation_type == "add_exercise" and operation.payload.get(
            "temporary_workout_id"
        ):
            raise RecommendationConflict(
                "Accept the grouped add-workout operation instead."
            )
        return [operation]
    temporary_id = str(operation.payload["temporary_id"])
    children = list(
        operation.recommendation.operations.filter(
            operation_type="add_exercise", status=RecommendationOperation.Status.PENDING
        ).order_by("created_at")
    )
    return [
        operation,
        *[
            child
            for child in children
            if str(child.payload.get("temporary_workout_id")) == temporary_id
        ],
    ]


def _apply_operations(*, user: Any, operations: list[RecommendationOperation]) -> None:
    """Apply operations atomically and mark unresolved targets stale on failure."""
    temporary_workouts: dict[str, Workout] = {}
    try:
        for operation in operations:
            _apply_operation(
                user=user, operation=operation, temporary_workouts=temporary_workouts
            )
            operation.status = RecommendationOperation.Status.ACCEPTED
            operation.resolved_at = timezone.now()
            operation.updated_by = "user"
            operation.save(
                update_fields=["status", "resolved_at", "updated_by", "updated_at"]
            )
    except (
        Exercise.DoesNotExist,
        Workout.DoesNotExist,
        WorkoutExercise.DoesNotExist,
        ValueError,
        KeyError,
    ) as exc:
        for operation in operations:
            if operation.status == RecommendationOperation.Status.PENDING:
                operation.status = RecommendationOperation.Status.STALE
                operation.resolved_at = timezone.now()
                operation.save(update_fields=["status", "resolved_at", "updated_at"])
        raise RecommendationConflict(
            "Recommendation target is no longer available."
        ) from exc


def _apply_operation(
    *,
    user: Any,
    operation: RecommendationOperation,
    temporary_workouts: dict[str, Workout],
) -> None:
    """Apply one persisted operation to the user's training data.

    Temporary workouts created earlier in the same batch are supplied through
    ``temporary_workouts`` so their child exercise operations can reference them.
    """
    payload = operation.payload
    operation_type = operation.operation_type
    if operation_type == "add_workout":
        temporary_workouts[str(payload["temporary_id"])] = Workout.objects.create(
            user_id=str(user.id),
            name=payload["name"],
            date=payload["date"],
            expected_time=payload.get("expected_time", 0),
        )
        return
    if operation_type == "add_exercise":
        workout = (
            temporary_workouts.get(str(payload.get("temporary_workout_id")))
            if payload.get("temporary_workout_id")
            else Workout.objects.get(pk=payload["workout_id"], user_id=str(user.id))
        )
        if workout is None:
            raise ValueError("Parent workout was not accepted.")
        exercise = Exercise.objects.get(
            pk=payload["exercise"]["id"], user_id__in=[str(user.id), ""]
        )
        prescription = payload["prescription"]
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sort_order=payload["position"],
            **prescription,
        )
        return
    if operation_type == "update_workout":
        workout = Workout.objects.get(pk=payload["workout_id"], user_id=str(user.id))
        for field, value in payload["changes"].items():
            setattr(workout, field, value)
        workout.save()
        return
    if operation_type == "remove_workout":
        Workout.objects.get(pk=payload["workout_id"], user_id=str(user.id)).delete()
        return
    workout_exercise = WorkoutExercise.objects.select_related("workout").get(
        pk=payload["workout_exercise_id"], workout__user_id=str(user.id)
    )
    if operation_type == "remove_exercise":
        workout_exercise.delete()
        return
    if operation_type == "update_exercise":
        for field, value in (payload.get("changes") or {}).items():
            setattr(workout_exercise, field, value)
        if payload.get("workout_id"):
            workout_exercise.workout = Workout.objects.get(
                pk=payload["workout_id"], user_id=str(user.id)
            )
        if payload.get("position") is not None:
            workout_exercise.sort_order = payload["position"]
        workout_exercise.save()
        return
    raise ValueError("Unsupported operation.")
