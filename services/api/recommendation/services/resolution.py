from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from recommendation.models import Recommendation, RecommendationOperation
from recommendation.services.errors import (
    RecommendationConflict,
    RecommendationNotFound,
)
from recommendation.services.presentation import refresh_coach_card_snapshot
from training.models import Exercise, Workout, WorkoutExercise


def get_recommendation(user: Any, recommendation_id: str) -> Recommendation | None:
    """Returns one user-owned recommendation and its operation ledger."""

    return (
        Recommendation.objects.filter(pk=recommendation_id, user=user)
        .prefetch_related("operations")
        .first()
    )


@transaction.atomic
def expire_run_recommendations(*, user: Any, run_id: UUID) -> int:
    """Expires active recommendations from a failed run and stales pending operations."""

    recommendations = Recommendation.objects.select_for_update().filter(
        user=user, run_id=run_id, status=Recommendation.Status.ACTIVE
    )
    now = timezone.now()
    recommendation_ids = list(recommendations.values_list("id", flat=True))
    if not recommendation_ids:
        return 0
    Recommendation.objects.filter(pk__in=recommendation_ids).update(
        status=Recommendation.Status.EXPIRED,
        expired_at=now,
        updated_at=now,
    )
    RecommendationOperation.objects.filter(
        recommendation_id__in=recommendation_ids,
        status=RecommendationOperation.Status.PENDING,
    ).update(
        status=RecommendationOperation.Status.STALE,
        resolved_at=now,
        updated_at=now,
    )
    for recommendation in recommendations:
        refresh_coach_card_snapshot(recommendation)
    return len(recommendation_ids)


@transaction.atomic
def reject_operation(
    *, user: Any, recommendation_id: str, operation_id: str
) -> Recommendation:
    """Rejects one pending operation without changing the remaining operations."""

    operation = _operation(user, recommendation_id, operation_id)
    if operation.status != RecommendationOperation.Status.PENDING:
        raise RecommendationConflict("Operation is no longer pending.")
    now = timezone.now()
    for bundled_operation in _operation_bundle(operation):
        if bundled_operation.status == RecommendationOperation.Status.PENDING:
            bundled_operation.status = RecommendationOperation.Status.REJECTED
            bundled_operation.resolved_at = now
            bundled_operation.save(update_fields=["status", "resolved_at", "updated_at"])
    _complete_if_resolved(operation.recommendation)
    refresh_coach_card_snapshot(operation.recommendation)
    return operation.recommendation


@transaction.atomic
def reject_recommendation(*, user: Any, recommendation_id: str) -> Recommendation:
    """Rejects every pending operation in a user-owned recommendation."""

    recommendation = get_recommendation(user, recommendation_id)
    if not recommendation:
        raise RecommendationNotFound("Recommendation was not found.")
    RecommendationOperation.objects.filter(
        recommendation=recommendation, status=RecommendationOperation.Status.PENDING
    ).update(status=RecommendationOperation.Status.REJECTED, resolved_at=timezone.now())
    _complete_if_resolved(recommendation)
    refresh_coach_card_snapshot(recommendation)
    return recommendation


@transaction.atomic
def accept_operation(
    *, user: Any, recommendation_id: str, operation_id: str
) -> Recommendation:
    """Applies one pending operation, with its dependent child operations if needed."""

    operation = _operation(user, recommendation_id, operation_id)
    if operation.status != RecommendationOperation.Status.PENDING:
        raise RecommendationConflict("Operation is no longer pending.")
    _apply_operations(user=user, operations=_operation_bundle(operation))
    _complete_if_resolved(operation.recommendation)
    refresh_coach_card_snapshot(operation.recommendation)
    return operation.recommendation


@transaction.atomic
def accept_recommendation(*, user: Any, recommendation_id: str) -> Recommendation:
    """Atomically applies every pending operation in a user-owned recommendation."""

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
    _complete_if_resolved(recommendation)
    refresh_coach_card_snapshot(recommendation)
    return recommendation


def _operation(
    user: Any, recommendation_id: str, operation_id: str
) -> RecommendationOperation:
    try:
        return RecommendationOperation.objects.select_related("recommendation").get(
            pk=operation_id,
            recommendation_id=recommendation_id,
            recommendation__user=user,
            recommendation__status=Recommendation.Status.ACTIVE,
        )
    except RecommendationOperation.DoesNotExist as exc:
        raise RecommendationNotFound("Recommendation operation was not found.") from exc


def _complete_if_resolved(recommendation: Recommendation) -> None:
    if not recommendation.operations.filter(
        status=RecommendationOperation.Status.PENDING
    ).exists():
        recommendation.status = Recommendation.Status.COMPLETED
        recommendation.save(update_fields=["status", "updated_at"])


def _operation_bundle(
    operation: RecommendationOperation,
) -> list[RecommendationOperation]:
    """Returns the operation set that must be accepted together."""

    if operation.operation_type != "add_workout":
        if (
            operation.operation_type == "add_exercise"
            and operation.payload["workout"]["kind"] == "new"
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
            if (
                child.payload["workout"]["kind"] == "new"
                and child.payload["workout"]["temporary_id"] == temporary_id
            )
        ],
    ]


def _apply_operations(*, user: Any, operations: list[RecommendationOperation]) -> None:
    """Applies operations and marks only unavailable targets stale."""

    temporary_workouts: dict[str, Workout] = {}
    try:
        for operation in operations:
            _apply_operation(
                user=user, operation=operation, temporary_workouts=temporary_workouts
            )
            operation.status = RecommendationOperation.Status.ACCEPTED
            operation.resolved_at = timezone.now()
            operation.save(update_fields=["status", "resolved_at", "updated_at"])
    except (
        Exercise.DoesNotExist,
        Workout.DoesNotExist,
        WorkoutExercise.DoesNotExist,
        ValueError,
        KeyError,
    ):
        for operation in operations:
            if operation.status == RecommendationOperation.Status.PENDING:
                operation.status = RecommendationOperation.Status.STALE
                operation.resolved_at = timezone.now()
                operation.save(update_fields=["status", "resolved_at", "updated_at"])
        # Stale is a successful resolution outcome: the user sees that the
        # proposal is no longer applicable without losing their own edit.
        return


def _apply_operation(
    *,
    user: Any,
    operation: RecommendationOperation,
    temporary_workouts: dict[str, Workout],
) -> None:
    """Applies one persisted recommendation operation to the user's training data."""

    payload = operation.payload
    operation_type = operation.operation_type
    if operation_type == "add_workout":
        workout = Workout.objects.create(
            user_id=str(user.id),
            name=payload["name"],
            date=payload["date"],
            expected_time=payload.get("expected_time", 0),
        )
        temporary_workouts[str(payload["temporary_id"])] = workout
        payload["created_workout_id"] = str(workout.id)
        operation.payload = payload
        operation.save(update_fields=["payload", "updated_at"])
        return
    if operation_type == "add_exercise":
        workout_reference = payload["workout"]
        workout = (
            temporary_workouts.get(workout_reference["temporary_id"])
            if workout_reference["kind"] == "new"
            else Workout.objects.get(
                pk=workout_reference["workout_id"], user_id=str(user.id)
            )
        )
        if workout is None:
            raise ValueError("Parent workout was not accepted.")
        exercise = Exercise.objects.get(
            pk=payload["exercise_id"], user_id__in=[str(user.id), ""]
        )
        prescription = payload["prescription"]
        workout_exercise_fields = (
            {
                "sets": prescription["sets"],
                "reps": prescription["reps"],
                "weight": prescription.get("weight"),
                "weight_unit": prescription.get("weight_unit", "lb"),
                "note": prescription.get("note", ""),
            }
            if prescription["type"] == "reps"
            else {
                "sets": prescription["sets"],
                "time": prescription["seconds"],
                "note": prescription.get("note", ""),
            }
        )
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sort_order=payload["position"],
            **workout_exercise_fields,
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
        if payload.get("target_workout_id"):
            workout_exercise.workout = Workout.objects.get(
                pk=payload["target_workout_id"], user_id=str(user.id)
            )
        if payload.get("position") is not None:
            workout_exercise.sort_order = payload["position"]
        workout_exercise.save()
        return
    raise ValueError("Unsupported operation.")
