from __future__ import annotations

from typing import Any, Protocol

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ai.recommendation.schemas import WorkoutPatchDraft
from ai.recommendation.services import WorkoutPatchGenerator
from recommendation.models import Recommendation, RecommendationOperation
from training.models import Exercise, Workout, WorkoutExercise
from whoop.exceptions import WhoopConnectionNotFound, WhoopError
from whoop.workflows.summary import disconnected_summary


class RecommendationNotFound(ValueError):
    pass


class RecommendationConflict(ValueError):
    pass


class RecommendationValidationError(ValueError):
    pass


WORKOUT_EXERCISE_UPDATE_FIELDS = {
    "sets",
    "reps",
    "time",
    "weight",
    "weight_unit",
    "note",
}

STRENGTH_UPDATE_FIELDS = {"sets", "reps", "weight", "weight_unit", "note"}
TIMED_UPDATE_FIELDS = {"time", "note"}


class WorkoutPatchDraftGenerator(Protocol):
    def generate(self, context: dict[str, Any]) -> WorkoutPatchDraft: ...


def build_workout_recommendation_context(
    user_id: str, workout_id: str
) -> dict[str, Any]:
    try:
        workout = Workout.objects.prefetch_related("workout_exercises__exercise").get(
            pk=workout_id, user_id=user_id
        )
    except Workout.DoesNotExist as exc:
        raise RecommendationNotFound("Workout was not found.") from exc

    if workout is None:
        raise RecommendationNotFound("Workout was not found.")

    return {
        "current_workout": {
            "id": str(workout.id),
            "version": workout.updated_at.isoformat(),
            "plan": str(workout.plan_id) if workout.plan_id else None,
            "name": workout.name,
            "date": workout.date.isoformat() if workout.date else None,
            "expected_time": workout.expected_time,
            "exercises": [
                {
                    "workout_exercise_id": str(workout_exercise.id),
                    "exercise_id": str(workout_exercise.exercise_id),
                    "name": workout_exercise.exercise.name,
                    "muscle_group": workout_exercise.exercise.muscle_group,
                    "default_sets": workout_exercise.exercise.default_sets,
                    "default_reps": workout_exercise.exercise.default_reps,
                    "default_time": workout_exercise.exercise.default_time,
                    "prescription_type": workout_exercise.exercise.prescription_type,
                    "exercise_notes": workout_exercise.exercise.notes,
                    "sets": workout_exercise.sets,
                    "reps": workout_exercise.reps,
                    "time": workout_exercise.time,
                    "weight": float(workout_exercise.weight)
                    if workout_exercise.weight is not None
                    else None,
                    "weight_unit": workout_exercise.weight_unit,
                    "note": workout_exercise.note,
                }
                for workout_exercise in workout.workout_exercises.all()
            ],
        },
        "available_exercises": [
            _exercise_catalog_item(exercise)
            for exercise in Exercise.objects.filter(
                Q(user_id=user_id) | Q(user_id="")
            ).order_by("name")
        ],
        "whoop_summary": _build_whoop_summary(user_id),
        "allowed_operations": [
            {
                "op": "replace_exercise",
                "target": "workout_exercise_id",
                "fields": ["workout_exercise_id", "replacement_exercise_id", "reason"],
            },
            {
                "op": "update_exercise",
                "target": "workout_exercise_id",
                "fields": ["workout_exercise_id", "changes", "reason"],
                "allowed_changes": sorted(WORKOUT_EXERCISE_UPDATE_FIELDS),
            },
            {
                "op": "remove_exercise",
                "target": "workout_exercise_id",
                "fields": ["workout_exercise_id", "reason"],
            },
            {
                "op": "add_exercise",
                "target": "exercise_id",
                "fields": [
                    "exercise_id",
                    "sets",
                    "reps",
                    "time",
                    "weight",
                    "weight_unit",
                    "note",
                    "reason",
                ],
            },
        ],
    }


def _build_whoop_summary(user_id: str) -> dict[str, Any]:
    from whoop import services as whoop_services

    try:
        return whoop_services.create_summary_service().execute(user_id)
    except WhoopConnectionNotFound:
        return disconnected_summary()
    except WhoopError as exc:
        return {
            "connected": False,
            "detail": f"WHOOP summary unavailable: {exc}",
        }
    except Exception as exc:
        return {
            "connected": False,
            "detail": f"WHOOP summary unavailable: {exc}",
        }


@transaction.atomic
def generate_recommendation_for_workout(
    user_id: str,
    workout_id: str,
    *,
    generator: WorkoutPatchDraftGenerator | None = None,
) -> Recommendation:
    context = build_workout_recommendation_context(user_id, workout_id)
    draft = (generator or WorkoutPatchGenerator()).generate(context)
    if not isinstance(draft, WorkoutPatchDraft):
        draft = WorkoutPatchDraft.model_validate(draft)

    operation_payloads = [
        operation.model_dump(mode="json", exclude_none=True)
        for operation in draft.operations
    ]
    _validate_operations(
        operations=operation_payloads,
        user_id=user_id,
        workout_id=workout_id,
    )

    recommendation = Recommendation.objects.create(
        user_id=user_id,
        workout_id=workout_id,
        snapshot_version=str(context["current_workout"]["version"]),
        status=Recommendation.Status.PENDING,
        summary=draft.summary,
        reason=draft.reason,
    )
    for index, payload in enumerate(operation_payloads, start=1):
        operation_type = str(payload.pop("op"))
        RecommendationOperation.objects.create(
            recommendation=recommendation,
            sequence=index,
            operation_type=operation_type,
            payload_json=payload,
        )
    return _recommendation_queryset().get(pk=recommendation.id)


def get_recommendation(user_id: str, recommendation_id: str) -> Recommendation | None:
    try:
        return _recommendation_queryset().get(pk=recommendation_id, user_id=user_id)
    except Recommendation.DoesNotExist:
        return None


def approve_recommendation(
    user_id: str,
    recommendation_id: str,
    *,
    expected_workout_version: str | None = None,
) -> Recommendation:
    raise RecommendationValidationError("Use operation-level approval.")


def approve_recommendation_operation(
    user_id: str,
    recommendation_id: str,
    operation_id: str,
    *,
    expected_workout_version: str | None = None,
) -> Recommendation:
    try:
        with transaction.atomic():
            recommendation = _get_recommendation_for_update(user_id, recommendation_id)
            operation = _get_operation_for_update(recommendation, operation_id)
            if operation.status != RecommendationOperation.Status.PENDING:
                raise RecommendationConflict("Recommendation operation is not pending.")

            try:
                workout = Workout.objects.select_for_update().get(
                    pk=recommendation.workout_id,
                    user_id=user_id,
                )
            except Workout.DoesNotExist as exc:
                raise RecommendationNotFound("Workout was not found.") from exc

            current_version = workout.updated_at.isoformat()
            expected = expected_workout_version or recommendation.snapshot_version
            if (
                current_version != recommendation.snapshot_version
                or current_version != expected
            ):
                raise RecommendationConflict(
                    "Workout changed since recommendation generation."
                )

            _apply_operation(workout, operation, user_id=user_id)
            workout.save()
            workout.refresh_from_db(fields=["updated_at"])
            now = timezone.now()
            operation.status = RecommendationOperation.Status.ACCEPTED
            operation.decided_at = now
            operation.applied_at = now
            operation.save(
                update_fields=["status", "decided_at", "applied_at", "updated_at"]
            )
            recommendation.snapshot_version = workout.updated_at.isoformat()
            recommendation.save(update_fields=["snapshot_version", "updated_at"])
            _refresh_recommendation_rollup(recommendation)
    except RecommendationNotFound:
        _mark_operation_status(
            user_id,
            recommendation_id,
            operation_id,
            RecommendationOperation.Status.FAILED,
        )
        raise
    except RecommendationConflict as exc:
        if str(exc) == "Workout changed since recommendation generation.":
            _mark_operation_status(
                user_id,
                recommendation_id,
                operation_id,
                RecommendationOperation.Status.STALE,
            )
        raise
    except Exception:
        _mark_operation_status(
            user_id,
            recommendation_id,
            operation_id,
            RecommendationOperation.Status.FAILED,
        )
        raise

    return _recommendation_queryset().get(pk=recommendation_id)


@transaction.atomic
def reject_recommendation(user_id: str, recommendation_id: str) -> Recommendation:
    raise RecommendationValidationError("Use operation-level rejection.")


@transaction.atomic
def reject_recommendation_operation(
    user_id: str,
    recommendation_id: str,
    operation_id: str,
) -> Recommendation:
    recommendation = _get_recommendation_for_update(user_id, recommendation_id)
    operation = _get_operation_for_update(recommendation, operation_id)
    if operation.status != RecommendationOperation.Status.PENDING:
        raise RecommendationConflict("Recommendation operation is not pending.")
    operation.status = RecommendationOperation.Status.REJECTED
    operation.decided_at = timezone.now()
    operation.save(update_fields=["status", "decided_at", "updated_at"])
    _refresh_recommendation_rollup(recommendation)
    return _recommendation_queryset().get(pk=recommendation.id)


def serialize_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    return {
        "id": str(recommendation.id),
        "user_id": recommendation.user_id,
        "workout_id": str(recommendation.workout_id),
        "snapshot_version": recommendation.snapshot_version,
        "status": recommendation.status,
        "summary": recommendation.summary,
        "reason": recommendation.reason,
        "operations": [
            _serialize_operation(
                operation, recommendation.user_id, str(recommendation.workout_id)
            )
            for operation in recommendation.operations.all().order_by("sequence")
        ],
        "created_at": recommendation.created_at.isoformat(),
        "updated_at": recommendation.updated_at.isoformat(),
    }


def _recommendation_queryset():
    return Recommendation.objects.prefetch_related("operations")


def _get_recommendation_for_update(
    user_id: str, recommendation_id: str
) -> Recommendation:
    try:
        return (
            Recommendation.objects.select_for_update()
            .prefetch_related("operations")
            .get(
                pk=recommendation_id,
                user_id=user_id,
            )
        )
    except Recommendation.DoesNotExist as exc:
        raise RecommendationNotFound("Recommendation was not found.") from exc


def _get_operation_for_update(
    recommendation: Recommendation,
    operation_id: str,
) -> RecommendationOperation:
    try:
        return RecommendationOperation.objects.select_for_update().get(
            pk=operation_id,
            recommendation=recommendation,
        )
    except RecommendationOperation.DoesNotExist as exc:
        raise RecommendationNotFound("Recommendation operation was not found.") from exc


def _mark_recommendation_status(
    user_id: str, recommendation_id: str, status: str
) -> None:
    Recommendation.objects.filter(pk=recommendation_id, user_id=user_id).update(
        status=status
    )


def _mark_operation_status(
    user_id: str,
    recommendation_id: str,
    operation_id: str,
    status: str,
) -> None:
    try:
        with transaction.atomic():
            recommendation = _get_recommendation_for_update(user_id, recommendation_id)
            operation = _get_operation_for_update(recommendation, operation_id)
            operation.status = status
            operation.decided_at = timezone.now()
            operation.save(update_fields=["status", "decided_at", "updated_at"])
            _refresh_recommendation_rollup(recommendation)
    except RecommendationNotFound:
        return


def _refresh_recommendation_rollup(recommendation: Recommendation) -> None:
    statuses = list(recommendation.operations.values_list("status", flat=True))
    if not statuses or RecommendationOperation.Status.PENDING in statuses:
        next_status = Recommendation.Status.PENDING
    elif all(status == RecommendationOperation.Status.ACCEPTED for status in statuses):
        next_status = Recommendation.Status.ACCEPTED
    elif all(status == RecommendationOperation.Status.REJECTED for status in statuses):
        next_status = Recommendation.Status.REJECTED
    else:
        next_status = Recommendation.Status.PARTIAL

    recommendation.status = next_status
    recommendation.save(update_fields=["status", "updated_at"])


def _validate_operations(
    *,
    operations: list[dict[str, Any]],
    user_id: str,
    workout_id: str,
) -> None:
    workout_exercises = {
        str(workout_exercise.id): workout_exercise
        for workout_exercise in WorkoutExercise.objects.select_related(
            "exercise"
        ).filter(
            workout_id=workout_id,
            workout__user_id=user_id,
        )
    }
    exercises = {
        str(exercise.id): exercise
        for exercise in Exercise.objects.filter(Q(user_id=user_id) | Q(user_id=""))
    }
    if not Workout.objects.filter(pk=workout_id, user_id=user_id).exists():
        raise RecommendationNotFound("Workout was not found.")

    for operation in operations:
        op = operation["op"]
        if op in {"replace_exercise", "update_exercise", "remove_exercise"}:
            if str(operation["workout_exercise_id"]) not in workout_exercises:
                raise RecommendationValidationError("Workout exercise was not found.")
        if (
            op == "replace_exercise"
            and str(operation["replacement_exercise_id"]) not in exercises
        ):
            raise RecommendationValidationError("Replacement exercise was not found.")
        if op == "add_exercise" and str(operation["exercise_id"]) not in exercises:
            raise RecommendationValidationError("Exercise was not found.")
        _validate_operation_prescription(
            operation,
            workout_exercises=workout_exercises,
            exercises=exercises,
        )


def _validate_operation_prescription(
    operation: dict[str, Any],
    *,
    workout_exercises: dict[str, WorkoutExercise],
    exercises: dict[str, Exercise],
) -> None:
    op = operation["op"]
    if op == "update_exercise":
        workout_exercise = workout_exercises[str(operation["workout_exercise_id"])]
        _normalize_update_changes_for_exercise(workout_exercise.exercise, operation)
        _validate_changes_for_exercise(
            workout_exercise.exercise,
            operation.get("changes", {}),
        )
    elif op == "add_exercise":
        exercise = exercises[str(operation["exercise_id"])]
        _normalize_add_payload_for_exercise(exercise, operation)
        _validate_add_payload_for_exercise(exercise, operation)


def _is_empty_prescription_value(value: Any) -> bool:
    return value is None or value == "" or value == 0 or value == 0.0


def _normalize_update_changes_for_exercise(
    exercise: Exercise, operation: dict[str, Any]
) -> None:
    changes = operation.get("changes")
    if not isinstance(changes, dict):
        return

    if exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        for field in ("sets", "reps", "weight"):
            if field in changes and _is_empty_prescription_value(changes[field]):
                changes.pop(field)
        if "weight_unit" in changes and "weight" not in changes:
            changes.pop("weight_unit")
    else:
        if "time" in changes and _is_empty_prescription_value(changes["time"]):
            changes.pop("time")


def _normalize_add_payload_for_exercise(
    exercise: Exercise, payload: dict[str, Any]
) -> None:
    if exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        for field in ("sets", "reps", "weight"):
            if field in payload and _is_empty_prescription_value(payload[field]):
                payload.pop(field)
        if "weight_unit" in payload and "weight" not in payload:
            payload.pop("weight_unit")
    else:
        if "time" in payload and _is_empty_prescription_value(payload["time"]):
            payload.pop("time")


def _validate_changes_for_exercise(exercise: Exercise, changes: dict[str, Any]) -> None:
    invalid_fields = set(changes) - WORKOUT_EXERCISE_UPDATE_FIELDS
    if invalid_fields:
        raise RecommendationValidationError("Unsupported workout exercise change.")
    if not changes:
        raise RecommendationValidationError(
            "update_exercise requires at least one change."
        )

    if exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        if set(changes) - TIMED_UPDATE_FIELDS:
            raise RecommendationValidationError(
                "Timed exercises can only use time and note."
            )
        return

    if set(changes) - STRENGTH_UPDATE_FIELDS:
        raise RecommendationValidationError(
            "Strength exercises can only use sets, reps, weight, and note."
        )
    if changes.get("time", 0) > 0:
        raise RecommendationValidationError(
            "Strength exercises can only use sets, reps, weight, and note."
        )


def _validate_add_payload_for_exercise(
    exercise: Exercise, payload: dict[str, Any]
) -> None:
    if exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        if (
            payload.get("sets", 0) > 0
            or payload.get("reps", 0) > 0
            or payload.get("weight") is not None
        ):
            raise RecommendationValidationError(
                "Timed exercises can only use time and note."
            )
        return

    if payload.get("time", 0) > 0:
        raise RecommendationValidationError(
            "Strength exercises can only use sets, reps, weight, and note."
        )


def _apply_operation(
    workout: Workout, operation: RecommendationOperation, *, user_id: str
) -> None:
    if operation.operation_type == RecommendationOperation.Type.REPLACE_EXERCISE:
        workout_exercise = _get_workout_exercise(
            workout, operation.payload_json["workout_exercise_id"]
        )
        workout_exercise.exercise = _get_exercise(
            operation.payload_json["replacement_exercise_id"], user_id=user_id
        )
        _normalize_workout_exercise_for_prescription(workout_exercise)
        workout_exercise.save(
            update_fields=[
                "exercise",
                "sets",
                "reps",
                "time",
                "weight",
                "weight_unit",
                "updated_at",
            ]
        )
        return

    if operation.operation_type == RecommendationOperation.Type.UPDATE_EXERCISE:
        workout_exercise = _get_workout_exercise(
            workout, operation.payload_json["workout_exercise_id"]
        )
        changes = operation.payload_json["changes"]
        _validate_changes_for_exercise(workout_exercise.exercise, changes)
        for field, value in changes.items():
            setattr(workout_exercise, field, value)
        workout_exercise.save(update_fields=[*changes.keys(), "updated_at"])
        return

    if operation.operation_type == RecommendationOperation.Type.REMOVE_EXERCISE:
        _get_workout_exercise(
            workout, operation.payload_json["workout_exercise_id"]
        ).delete()
        return

    if operation.operation_type == RecommendationOperation.Type.ADD_EXERCISE:
        payload = operation.payload_json
        exercise = _get_exercise(payload["exercise_id"], user_id=user_id)
        _validate_add_payload_for_exercise(exercise, payload)
        WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sets=payload.get("sets", 0),
            reps=payload.get("reps", 0),
            time=payload.get("time", 0),
            weight=payload.get("weight"),
            weight_unit=payload.get("weight_unit", "lb"),
            note=payload.get("note", ""),
        )
        return

    raise RecommendationValidationError("Unsupported recommendation operation.")


def _get_workout_exercise(
    workout: Workout, workout_exercise_id: str
) -> WorkoutExercise:
    try:
        return WorkoutExercise.objects.get(pk=workout_exercise_id, workout=workout)
    except WorkoutExercise.DoesNotExist as exc:
        raise RecommendationValidationError("Workout exercise was not found.") from exc


def _get_exercise(exercise_id: str, *, user_id: str) -> Exercise:
    try:
        return Exercise.objects.get(Q(user_id=user_id) | Q(user_id=""), pk=exercise_id)
    except Exercise.DoesNotExist as exc:
        raise RecommendationValidationError("Exercise was not found.") from exc


def _normalize_workout_exercise_for_prescription(
    workout_exercise: WorkoutExercise,
) -> None:
    if workout_exercise.exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        workout_exercise.sets = 0
        workout_exercise.reps = 0
        workout_exercise.weight = None
        workout_exercise.weight_unit = "lb"
        if workout_exercise.time == 0:
            workout_exercise.time = workout_exercise.exercise.default_time
        return

    workout_exercise.time = 0
    if workout_exercise.sets == 0:
        workout_exercise.sets = workout_exercise.exercise.default_sets
    if workout_exercise.reps == 0:
        workout_exercise.reps = workout_exercise.exercise.default_reps
    if not workout_exercise.weight_unit:
        workout_exercise.weight_unit = "lb"


def _serialize_operation(
    operation: RecommendationOperation,
    user_id: str,
    workout_id: str,
) -> dict[str, Any]:
    return {
        "id": str(operation.id),
        "sequence": operation.sequence,
        "operation_type": operation.operation_type,
        "status": operation.status,
        "payload": operation.payload_json,
        "display_text": _display_text(operation, user_id, workout_id),
    }


def _display_text(
    operation: RecommendationOperation, user_id: str, workout_id: str
) -> str:
    payload = operation.payload_json
    if operation.operation_type == RecommendationOperation.Type.REPLACE_EXERCISE:
        current = _workout_exercise_name(payload["workout_exercise_id"], workout_id)
        replacement = _exercise_name(payload["replacement_exercise_id"], user_id)
        return f"Replace {current} with {replacement}"
    if operation.operation_type == RecommendationOperation.Type.UPDATE_EXERCISE:
        current = _workout_exercise_name(payload["workout_exercise_id"], workout_id)
        changes = ", ".join(
            f"{key} to {value}" for key, value in payload["changes"].items()
        )
        return f"Update {current}: {changes}"
    if operation.operation_type == RecommendationOperation.Type.REMOVE_EXERCISE:
        current = _workout_exercise_name(payload["workout_exercise_id"], workout_id)
        return f"Remove {current}"
    if operation.operation_type == RecommendationOperation.Type.ADD_EXERCISE:
        exercise = _exercise_name(payload["exercise_id"], user_id)
        return f"Add {exercise}"
    return "Unsupported recommendation operation"


def _workout_exercise_name(workout_exercise_id: str, workout_id: str) -> str:
    try:
        return (
            WorkoutExercise.objects.select_related("exercise")
            .get(
                pk=workout_exercise_id,
                workout_id=workout_id,
            )
            .exercise.name
        )
    except WorkoutExercise.DoesNotExist:
        return str(workout_exercise_id)


def _exercise_name(exercise_id: str, user_id: str) -> str:
    try:
        return Exercise.objects.get(
            Q(user_id=user_id) | Q(user_id=""), pk=exercise_id
        ).name
    except Exercise.DoesNotExist:
        return str(exercise_id)


def _exercise_catalog_item(exercise: Exercise) -> dict[str, Any]:
    return {
        "id": str(exercise.id),
        "name": exercise.name,
        "prescription_type": exercise.prescription_type,
        "default_sets": exercise.default_sets,
        "default_reps": exercise.default_reps,
        "muscle_group": exercise.muscle_group,
        "default_time": exercise.default_time,
        "notes": exercise.notes,
    }
