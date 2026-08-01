from __future__ import annotations

from typing import Any

from ai.recommendation.schemas import WorkoutPatchDraft
from django.db import transaction
from django.db.models import Max, Q
from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise

from recommendation.models import Recommendation


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
EXERCISE_OPERATION_TYPES = {
    Recommendation.OperationType.ADD_EXERCISE,
    Recommendation.OperationType.REMOVE_EXERCISE,
    Recommendation.OperationType.REPLACE_EXERCISE,
    Recommendation.OperationType.UPDATE_EXERCISE,
    Recommendation.OperationType.MOVE_EXERCISE,
}


@transaction.atomic
def create_recommendation_from_workout_patch(
    *,
    user_id: str,
    workout_id: str,
    draft: WorkoutPatchDraft,
    snapshot_version: str | None = None,
    source: str = Recommendation.Source.DAILY_RECOMMENDATION,
    coach_conversation_id: str | None = None,
    coach_message_id: str | None = None,
) -> Recommendation:
    if not isinstance(draft, WorkoutPatchDraft):
        draft = WorkoutPatchDraft.model_validate(draft)
    if snapshot_version is None:
        snapshot_version = _get_workout(workout_id, user_id=user_id).updated_at.isoformat()

    operation_payload = draft.operation.model_dump(mode="json", exclude_none=True)
    operation_type = str(operation_payload.pop("op"))
    _validate_operation(
        operation_type=operation_type,
        payload=operation_payload,
        user_id=user_id,
        workout_id=workout_id,
    )
    _validate_pending_recommendation_coexistence(
        user_id=user_id,
        workout_id=workout_id,
        operation_type=operation_type,
    )

    return Recommendation.objects.create(
        user_id=user_id,
        workout_id=workout_id,
        snapshot_version=snapshot_version,
        status=Recommendation.Status.PENDING,
        summary=draft.summary,
        reason=draft.reason,
        operation_type=operation_type,
        payload_json=operation_payload,
        source=source,
        coach_conversation_id=coach_conversation_id,
        coach_message_id=coach_message_id,
    )


def list_recommendations(
    user_id: str, *, status: str | None = None
) -> list[Recommendation]:
    queryset = Recommendation.objects.filter(user_id=user_id)
    if status:
        queryset = queryset.filter(status=status)
    return list(queryset.order_by("-created_at"))


def get_recommendation(user_id: str, recommendation_id: str) -> Recommendation | None:
    try:
        return Recommendation.objects.get(pk=recommendation_id, user_id=user_id)
    except Recommendation.DoesNotExist:
        return None


@transaction.atomic
def update_recommendation_status(
    user_id: str, recommendation_id: str, *, status: str
) -> Recommendation:
    recommendation = _get_recommendation_for_update(user_id, recommendation_id)
    if status not in {choice.value for choice in Recommendation.Status}:
        raise RecommendationValidationError("Unsupported recommendation status.")
    if recommendation.status != Recommendation.Status.PENDING:
        raise RecommendationConflict("Recommendation is no longer pending.")
    if status == Recommendation.Status.APPLIED:
        return accept_recommendation(user_id, recommendation_id)
    recommendation.status = status
    recommendation.save(update_fields=["status", "updated_at"])
    return recommendation


def accept_recommendation(
    user_id: str,
    recommendation_id: str,
    *,
    expected_workout_version: str | None = None,
) -> Recommendation:
    try:
        with transaction.atomic():
            recommendation = _get_recommendation_for_update(user_id, recommendation_id)
            if recommendation.status != Recommendation.Status.PENDING:
                raise RecommendationConflict("Recommendation is no longer pending.")

            try:
                workout = Workout.objects.select_for_update().get(
                    pk=recommendation.workout_id,
                    user_id=user_id,
                )
            except Workout.DoesNotExist as exc:
                raise RecommendationNotFound("Workout was not found.") from exc

            current_version = workout.updated_at.isoformat()
            expected = expected_workout_version or recommendation.snapshot_version
            if current_version != recommendation.snapshot_version or current_version != expected:
                raise RecommendationConflict("Workout changed since recommendation generation.")

            touch_workout = _apply_operation(
                workout,
                recommendation.operation_type,
                recommendation.payload_json,
                user_id=user_id,
            )
            if touch_workout:
                workout.save()
            if Workout.objects.filter(pk=workout.id, user_id=user_id).exists():
                workout.refresh_from_db(fields=["updated_at"])
                recommendation.snapshot_version = workout.updated_at.isoformat()
            recommendation.status = Recommendation.Status.APPLIED
            recommendation.save(update_fields=["snapshot_version", "status", "updated_at"])
    except RecommendationNotFound:
        _mark_recommendation_status(user_id, recommendation_id, Recommendation.Status.FAILED)
        raise
    except RecommendationConflict as exc:
        if str(exc) == "Workout changed since recommendation generation.":
            _mark_recommendation_status(user_id, recommendation_id, Recommendation.Status.STALE)
        raise
    except Exception:
        _mark_recommendation_status(user_id, recommendation_id, Recommendation.Status.FAILED)
        raise
    recommendation = get_recommendation(user_id, recommendation_id)
    if recommendation is None:
        raise RecommendationNotFound("Recommendation was not found.")
    return recommendation


@transaction.atomic
def reject_recommendation(user_id: str, recommendation_id: str) -> Recommendation:
    recommendation = _get_recommendation_for_update(user_id, recommendation_id)
    if recommendation.status != Recommendation.Status.PENDING:
        raise RecommendationConflict("Recommendation is no longer pending.")
    recommendation.status = Recommendation.Status.REJECTED
    recommendation.save(update_fields=["status", "updated_at"])
    return recommendation


def serialize_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    return {
        "id": str(recommendation.id),
        "user_id": recommendation.user_id,
        "workout_id": str(recommendation.workout_id),
        "snapshot_version": recommendation.snapshot_version,
        "status": recommendation.status,
        "summary": recommendation.summary,
        "reason": recommendation.reason,
        "source": recommendation.source,
        "coach_conversation_id": str(recommendation.coach_conversation_id)
        if recommendation.coach_conversation_id
        else None,
        "coach_message_id": str(recommendation.coach_message_id)
        if recommendation.coach_message_id
        else None,
        "operation_type": recommendation.operation_type,
        "payload": recommendation.payload_json,
        "display_text": _display_text(
            recommendation.operation_type,
            recommendation.payload_json,
            recommendation.user_id,
            str(recommendation.workout_id),
        ),
        "created_at": recommendation.created_at.isoformat(),
        "updated_at": recommendation.updated_at.isoformat(),
    }


def _get_recommendation_for_update(
    user_id: str, recommendation_id: str
) -> Recommendation:
    try:
        return Recommendation.objects.select_for_update().get(
            pk=recommendation_id,
            user_id=user_id,
        )
    except Recommendation.DoesNotExist as exc:
        raise RecommendationNotFound("Recommendation was not found.") from exc


def _validate_pending_recommendation_coexistence(
    *, user_id: str, workout_id: str, operation_type: str
) -> None:
    pending_types = set(
        Recommendation.objects.filter(
            user_id=user_id,
            workout_id=workout_id,
            status=Recommendation.Status.PENDING,
        ).values_list("operation_type", flat=True)
    )
    if operation_type == Recommendation.OperationType.REVISE_WORKOUT and (
        pending_types & EXERCISE_OPERATION_TYPES
    ):
        raise RecommendationValidationError(
            "ReviseWorkout cannot coexist with exercise recommendations for the same workout."
        )
    if operation_type in EXERCISE_OPERATION_TYPES and (
        Recommendation.OperationType.REVISE_WORKOUT in pending_types
    ):
        raise RecommendationValidationError(
            "Exercise recommendations cannot coexist with ReviseWorkout for the same workout."
        )
    if operation_type == Recommendation.OperationType.REMOVE_WORKOUT and pending_types:
        raise RecommendationValidationError(
            "RemoveWorkout cannot coexist with child workout recommendations."
        )
    if pending_types and Recommendation.OperationType.REMOVE_WORKOUT in pending_types:
        raise RecommendationValidationError(
            "Recommendations cannot coexist with RemoveWorkout for the same workout."
        )


def _validate_operation(
    *,
    operation_type: str,
    payload: dict[str, Any],
    user_id: str,
    workout_id: str,
) -> None:
    if operation_type not in {choice.value for choice in Recommendation.OperationType}:
        raise RecommendationValidationError("Unsupported recommendation operation.")
    if operation_type in {
        Recommendation.OperationType.REMOVE_EXERCISE,
        Recommendation.OperationType.REPLACE_EXERCISE,
        Recommendation.OperationType.UPDATE_EXERCISE,
        Recommendation.OperationType.MOVE_EXERCISE,
    }:
        _get_workout_exercise(
            _get_workout(workout_id, user_id=user_id),
            payload["workout_exercise_id"],
        )
    if operation_type == Recommendation.OperationType.REPLACE_EXERCISE:
        replacement_id = _replacement_exercise_id(payload)
        _get_exercise(replacement_id, user_id=user_id)
    if operation_type == Recommendation.OperationType.ADD_EXERCISE:
        _get_exercise(_add_exercise_id(payload), user_id=user_id)
    if operation_type == Recommendation.OperationType.UPDATE_EXERCISE:
        changes = _operation_changes(payload)
        workout_exercise = _get_workout_exercise(
            _get_workout(workout_id, user_id=user_id),
            payload["workout_exercise_id"],
        )
        _normalize_update_changes_for_exercise(workout_exercise.exercise, changes)
        _validate_changes_for_exercise(workout_exercise.exercise, changes)
        payload["changes"] = changes
    if operation_type in {
        Recommendation.OperationType.REMOVE_WORKOUT,
        Recommendation.OperationType.UPDATE_WORKOUT,
        Recommendation.OperationType.REVISE_WORKOUT,
    }:
        target_workout_id = payload.get("workout_id") or workout_id
        _get_workout(str(target_workout_id), user_id=user_id)
    if operation_type == Recommendation.OperationType.ADD_WORKOUT:
        _get_training_plan(str(payload["training_plan_id"]), user_id=user_id)


def _operation_changes(payload: dict[str, Any]) -> dict[str, Any]:
    changes = payload.get("changes") or payload.get("prescription_changes") or {}
    if "notes" in changes and "note" not in changes:
        changes["note"] = changes.pop("notes")
    changes.pop("rest_seconds", None)
    return changes


def _replacement_exercise_id(payload: dict[str, Any]) -> str:
    if payload.get("replacement_exercise_id"):
        return str(payload["replacement_exercise_id"])
    replacement = payload.get("replacement") or {}
    return str(replacement["exercise_definition_id"])


def _add_exercise_id(payload: dict[str, Any]) -> str:
    if payload.get("exercise_id"):
        return str(payload["exercise_id"])
    exercise = payload.get("exercise") or {}
    return str(exercise["exercise_definition_id"])


def _prescription_values(payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("exercise") or payload.get("replacement") or payload
    result = {
        "sets": source.get("sets", 0),
        "reps": source.get("reps", 0),
        "weight": source.get("weight"),
    }
    if source.get("notes") is not None:
        result["note"] = source.get("notes")
    if source.get("note") is not None:
        result["note"] = source.get("note")
    return result


def _mark_recommendation_status(
    user_id: str, recommendation_id: str, status: str
) -> None:
    Recommendation.objects.filter(pk=recommendation_id, user_id=user_id).update(
        status=status
    )


def _apply_operation(
    workout: Workout, operation_type: str, payload: dict[str, Any], *, user_id: str
) -> bool:
    if operation_type == Recommendation.OperationType.REPLACE_EXERCISE:
        workout_exercise = _get_workout_exercise(workout, payload["workout_exercise_id"])
        workout_exercise.exercise = _get_exercise(_replacement_exercise_id(payload), user_id=user_id)
        values = _prescription_values(payload)
        for field, value in values.items():
            setattr(workout_exercise, field, value)
        _normalize_workout_exercise_for_prescription(workout_exercise)
        workout_exercise.save()
        return True

    if operation_type == Recommendation.OperationType.UPDATE_EXERCISE:
        workout_exercise = _get_workout_exercise(workout, payload["workout_exercise_id"])
        changes = _operation_changes(payload)
        _validate_changes_for_exercise(workout_exercise.exercise, changes)
        for field, value in changes.items():
            setattr(workout_exercise, field, value)
        workout_exercise.save()
        return True

    if operation_type == Recommendation.OperationType.REMOVE_EXERCISE:
        _get_workout_exercise(workout, payload["workout_exercise_id"]).delete()
        return True

    if operation_type == Recommendation.OperationType.ADD_EXERCISE:
        exercise = _get_exercise(_add_exercise_id(payload), user_id=user_id)
        values = _prescription_values(payload)
        workout_exercise = WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sets=values.get("sets", 0),
            reps=values.get("reps", 0),
            weight=values.get("weight"),
            note=values.get("note", ""),
            sort_order=_next_workout_exercise_order(workout),
        )
        _normalize_workout_exercise_for_prescription(workout_exercise)
        workout_exercise.save()
        return True

    if operation_type == Recommendation.OperationType.MOVE_EXERCISE:
        workout_exercise = _get_workout_exercise(workout, payload["workout_exercise_id"])
        _move_workout_exercise(workout_exercise, payload.get("after_workout_exercise_id"))
        return True

    if operation_type == Recommendation.OperationType.ADD_WORKOUT:
        training_plan = _get_training_plan(str(payload["training_plan_id"]), user_id=user_id)
        draft = payload["workout"]
        new_workout = Workout.objects.create(
            user_id=user_id,
            plan=training_plan,
            name=draft["name"],
            date=draft["date"],
            expected_time=0,
        )
        for prescription in draft.get("exercises", []):
            _create_workout_exercise_from_prescription(new_workout, prescription, user_id=user_id)
        return False

    if operation_type == Recommendation.OperationType.REMOVE_WORKOUT:
        _get_workout(str(payload.get("workout_id") or workout.id), user_id=user_id).delete()
        return False

    if operation_type == Recommendation.OperationType.UPDATE_WORKOUT:
        target = _get_workout(str(payload.get("workout_id") or workout.id), user_id=user_id)
        changes = payload["workout_changes"]
        if changes.get("name") is not None:
            target.name = changes["name"]
        if changes.get("date") is not None:
            target.date = changes["date"]
        target.save()
        return False

    if operation_type == Recommendation.OperationType.REVISE_WORKOUT:
        target = _get_workout(str(payload.get("workout_id") or workout.id), user_id=user_id)
        draft = payload["proposed_workout"]
        target.name = draft["name"]
        target.date = draft["date"]
        target.save()
        target.workout_exercises.all().delete()
        for prescription in draft.get("exercises", []):
            _create_workout_exercise_from_prescription(target, prescription, user_id=user_id)
        return False

    raise RecommendationValidationError("Unsupported recommendation operation.")


def _get_workout(workout_id: str, *, user_id: str) -> Workout:
    try:
        return Workout.objects.get(pk=workout_id, user_id=user_id)
    except Workout.DoesNotExist as exc:
        raise RecommendationNotFound("Workout was not found.") from exc


def _get_training_plan(training_plan_id: str, *, user_id: str) -> TrainingPlan:
    try:
        return TrainingPlan.objects.get(pk=training_plan_id, user_id=user_id)
    except TrainingPlan.DoesNotExist as exc:
        raise RecommendationValidationError("Training plan was not found.") from exc


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


def _validate_changes_for_exercise(exercise: Exercise, changes: dict[str, Any]) -> None:
    invalid_fields = set(changes) - WORKOUT_EXERCISE_UPDATE_FIELDS
    if invalid_fields:
        raise RecommendationValidationError("Unsupported workout exercise change.")
    if not changes:
        raise RecommendationValidationError("update_exercise requires at least one change.")

    if exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        if set(changes) - TIMED_UPDATE_FIELDS:
            raise RecommendationValidationError("Timed exercises can only use time and note.")
        return

    if set(changes) - STRENGTH_UPDATE_FIELDS:
        raise RecommendationValidationError(
            "Strength exercises can only use sets, reps, weight, and note."
        )


def _is_empty_prescription_value(value: Any) -> bool:
    return value is None or value == "" or value == 0 or value == 0.0


def _normalize_update_changes_for_exercise(
    exercise: Exercise, changes: dict[str, Any]
) -> None:
    if exercise.prescription_type == Exercise.PrescriptionType.TIMED:
        for field in ("sets", "reps", "weight"):
            if field in changes and _is_empty_prescription_value(changes[field]):
                changes.pop(field)
        if "weight_unit" in changes and "weight" not in changes:
            changes.pop("weight_unit")
    else:
        if "time" in changes and _is_empty_prescription_value(changes["time"]):
            changes.pop("time")


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


def _next_workout_exercise_order(workout: Workout) -> int:
    value = (
        WorkoutExercise.objects.filter(workout=workout).aggregate(Max("sort_order"))[
            "sort_order__max"
        ]
        or 0
    )
    return int(value) + 1


def _move_workout_exercise(
    workout_exercise: WorkoutExercise, after_workout_exercise_id: str | None
) -> None:
    siblings = list(
        WorkoutExercise.objects.filter(workout=workout_exercise.workout)
        .exclude(pk=workout_exercise.id)
        .order_by("sort_order", "created_at", "exercise__name")
    )
    _reorder_object(workout_exercise, siblings, after_workout_exercise_id)


def _reorder_object(
    target: WorkoutExercise,
    siblings: list[WorkoutExercise],
    after_id: str | None,
) -> None:
    insert_at = 0
    if after_id:
        for index, sibling in enumerate(siblings):
            if str(sibling.id) == str(after_id):
                insert_at = index + 1
                break
    ordered = [*siblings]
    ordered.insert(insert_at, target)
    for index, item in enumerate(ordered, start=1):
        item.sort_order = index
        item.save(update_fields=["sort_order", "updated_at"])


def _create_workout_exercise_from_prescription(
    workout: Workout, prescription: dict[str, Any], *, user_id: str
) -> WorkoutExercise:
    exercise = _get_exercise(str(prescription["exercise_definition_id"]), user_id=user_id)
    workout_exercise = WorkoutExercise.objects.create(
        workout=workout,
        exercise=exercise,
        sets=prescription.get("sets") or 0,
        reps=prescription.get("reps") or 0,
        weight=prescription.get("weight"),
        note=prescription.get("notes") or "",
        sort_order=_next_workout_exercise_order(workout),
    )
    _normalize_workout_exercise_for_prescription(workout_exercise)
    workout_exercise.save()
    return workout_exercise


def _display_text(
    operation_type: str, payload: dict[str, Any], user_id: str, workout_id: str
) -> str:
    if operation_type == Recommendation.OperationType.REPLACE_EXERCISE:
        if "workout_exercise_id" not in payload:
            return "Replace exercise"
        current = _workout_exercise_name(payload["workout_exercise_id"], workout_id)
        replacement = _exercise_name(_replacement_exercise_id(payload), user_id)
        return f"Replace {current} with {replacement}"
    if operation_type == Recommendation.OperationType.UPDATE_EXERCISE:
        if "workout_exercise_id" not in payload:
            return "Update exercise"
        current = _workout_exercise_name(payload["workout_exercise_id"], workout_id)
        changes = ", ".join(
            f"{key} to {value}" for key, value in _operation_changes(payload).items()
        )
        return f"Update {current}: {changes}"
    if operation_type == Recommendation.OperationType.REMOVE_EXERCISE:
        if "workout_exercise_id" not in payload:
            return "Remove exercise"
        current = _workout_exercise_name(payload["workout_exercise_id"], workout_id)
        return f"Remove {current}"
    if operation_type == Recommendation.OperationType.ADD_EXERCISE:
        exercise = _exercise_name(_add_exercise_id(payload), user_id)
        return f"Add {exercise}"
    if operation_type == Recommendation.OperationType.REVISE_WORKOUT:
        return "Revise workout"
    if operation_type == Recommendation.OperationType.REMOVE_WORKOUT:
        return "Remove workout"
    if operation_type == Recommendation.OperationType.UPDATE_WORKOUT:
        return "Update workout"
    if operation_type == Recommendation.OperationType.ADD_WORKOUT:
        return "Add workout"
    if operation_type == Recommendation.OperationType.MOVE_EXERCISE:
        return "Move exercise"
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
