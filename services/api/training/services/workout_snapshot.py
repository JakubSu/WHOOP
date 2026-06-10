from typing import Any

from django.db import transaction
from django.db.models import Prefetch, Q

from training.domain import ExerciseSummary, WorkoutSnapshot, WorkoutSnapshotExercise
from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise


class StaleWorkoutSnapshotVersion(ValueError):
    pass


def list_workout_snapshots(user_id: str) -> list[WorkoutSnapshot]:
    return [
        _snapshot_from_workout(workout)
        for workout in _workout_queryset().filter(user_id=user_id)
    ]


def get_workout_snapshot(workout_id: str, user_id: str) -> WorkoutSnapshot | None:
    try:
        workout = _workout_queryset().get(pk=workout_id, user_id=user_id)
    except Workout.DoesNotExist:
        return None
    return _snapshot_from_workout(workout)


@transaction.atomic
def create_workout_snapshot(data: dict[str, Any], *, user_id: str) -> WorkoutSnapshot:
    exercises = list(data.get("exercises", []))
    workout = Workout.objects.create(**_normalized_workout_payload(data, user_id=user_id))
    _replace_workout_exercises(workout, exercises, user_id=user_id)
    workout.save()
    return get_workout_snapshot(str(workout.id), user_id)  # type: ignore[return-value]


@transaction.atomic
def update_workout_snapshot(workout_id: str, data: dict[str, Any], *, user_id: str) -> WorkoutSnapshot:
    try:
        workout = Workout.objects.select_for_update().get(pk=workout_id, user_id=user_id)
    except Workout.DoesNotExist as exc:
        raise ValueError("Workout was not found.") from exc

    expected_version = data.get("expected_version")
    current_version = _version_from_workout(workout)
    if expected_version is not None and str(expected_version) != current_version:
        raise StaleWorkoutSnapshotVersion("Workout snapshot version is stale.")

    payload = _normalized_workout_payload(data, existing=workout, user_id=user_id)
    for field, value in payload.items():
        setattr(workout, field, value)
    workout.save()

    if "exercises" in data:
        _replace_workout_exercises(workout, list(data["exercises"]), user_id=user_id)
        workout.save()

    return get_workout_snapshot(str(workout.id), user_id)  # type: ignore[return-value]


def delete_workout_snapshot(workout_id: str, *, user_id: str) -> None:
    try:
        workout = Workout.objects.get(pk=workout_id, user_id=user_id)
    except Workout.DoesNotExist as exc:
        raise ValueError("Workout was not found.") from exc
    workout.delete()


def _workout_queryset():
    return Workout.objects.prefetch_related(
        Prefetch(
            "workout_exercises",
            queryset=WorkoutExercise.objects.select_related("exercise").order_by("position"),
        )
    )


def _snapshot_from_workout(workout: Workout) -> WorkoutSnapshot:
    return WorkoutSnapshot(
        id=str(workout.id),
        user_id=workout.user_id,
        version=_version_from_workout(workout),
        training_plan=str(workout.training_plan_id) if workout.training_plan_id else None,
        scheduled_date=workout.scheduled_date,
        name=workout.name,
        workout_type=workout.workout_type,
        status=workout.status,
        planned_intensity=workout.planned_intensity,
        planned_duration_minutes=workout.planned_duration_minutes,
        completed_at=workout.completed_at,
        actual_strain=workout.actual_strain,
        notes=workout.notes,
        exercises=[
            _snapshot_exercise_from_model(workout_exercise)
            for workout_exercise in workout.workout_exercises.all()
        ],
        created_at=workout.created_at,
        updated_at=workout.updated_at,
    )


def _snapshot_exercise_from_model(workout_exercise: WorkoutExercise) -> WorkoutSnapshotExercise:
    workout_exercise_id = str(workout_exercise.id)
    exercise = workout_exercise.exercise
    return WorkoutSnapshotExercise(
        workout_exercise_id=workout_exercise_id,
        snapshot_exercise_key=workout_exercise_id,
        exercise=ExerciseSummary(
            id=str(exercise.id),
            name=exercise.name,
            category=exercise.category,
            primary_muscle_group=exercise.primary_muscle_group,
            secondary_muscle_groups=list(exercise.secondary_muscle_groups),
            equipment=exercise.equipment,
            default_intensity=exercise.default_intensity,
            is_favorite=exercise.is_favorite,
            is_avoided=exercise.is_avoided,
            notes=exercise.notes,
        ),
        position=workout_exercise.position,
        sets=workout_exercise.sets,
        reps=workout_exercise.reps,
        duration_seconds=workout_exercise.duration_seconds,
        distance=workout_exercise.distance,
        load=workout_exercise.load,
        intensity=workout_exercise.intensity,
        rest_seconds=workout_exercise.rest_seconds,
        notes=workout_exercise.notes,
    )


def _normalized_workout_payload(
    data: dict[str, Any],
    existing: Workout | None = None,
    *,
    user_id: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"user_id": user_id}
    if "training_plan" in data:
        payload["training_plan"] = _get_training_plan(data["training_plan"], user_id=user_id)
    elif existing is not None:
        payload["training_plan"] = existing.training_plan

    fields = (
        "scheduled_date",
        "name",
        "workout_type",
        "status",
        "planned_intensity",
        "planned_duration_minutes",
        "completed_at",
        "actual_strain",
        "notes",
    )
    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    payload.pop("expected_version", None)
    payload.pop("exercises", None)
    return payload


def _replace_workout_exercises(
    workout: Workout,
    exercise_payloads: list[dict[str, Any]],
    *,
    user_id: str,
) -> None:
    existing = {
        str(workout_exercise.id): workout_exercise
        for workout_exercise in WorkoutExercise.objects.select_related("exercise").filter(workout=workout)
    }
    referenced_ids = {
        str(item["workout_exercise_id"])
        for item in exercise_payloads
        if item.get("workout_exercise_id")
    }
    missing_ids = referenced_ids - set(existing)
    if missing_ids:
        raise ValueError("Workout exercise was not found.")

    for workout_exercise_id, workout_exercise in existing.items():
        if workout_exercise_id not in referenced_ids:
            workout_exercise.delete()

    kept = [existing[workout_exercise_id] for workout_exercise_id in referenced_ids]
    for index, workout_exercise in enumerate(kept, start=1):
        workout_exercise.position = 100000 + index
        workout_exercise.save(update_fields=["position"])

    for item in exercise_payloads:
        workout_exercise_id = item.get("workout_exercise_id")
        if workout_exercise_id:
            workout_exercise = existing[str(workout_exercise_id)]
            _apply_workout_exercise_payload(workout_exercise, item, user_id=user_id)
            workout_exercise.save()
        else:
            WorkoutExercise.objects.create(
                workout=workout,
                **_normalized_workout_exercise_payload(item, user_id=user_id),
            )


def _apply_workout_exercise_payload(
    workout_exercise: WorkoutExercise,
    data: dict[str, Any],
    *,
    user_id: str,
) -> None:
    payload = _normalized_workout_exercise_payload(data, user_id=user_id)
    for field, value in payload.items():
        setattr(workout_exercise, field, value)


def _normalized_workout_exercise_payload(data: dict[str, Any], *, user_id: str) -> dict[str, Any]:
    return {
        "exercise": _get_exercise(data["exercise"], user_id=user_id),
        "position": data.get("position", 1),
        "sets": data.get("sets", 0),
        "reps": data.get("reps", 0),
        "duration_seconds": data.get("duration_seconds", 0),
        "distance": data.get("distance", "0.00"),
        "load": data.get("load", "0.00"),
        "intensity": data.get("intensity", ""),
        "rest_seconds": data.get("rest_seconds", 0),
        "notes": data.get("notes", ""),
    }


def _get_training_plan(training_plan_value: TrainingPlan | str | None, *, user_id: str) -> TrainingPlan | None:
    if not training_plan_value:
        return None

    if isinstance(training_plan_value, TrainingPlan):
        if training_plan_value.user_id != user_id:
            raise ValueError("Training plan was not found.")
        return training_plan_value

    try:
        return TrainingPlan.objects.get(pk=training_plan_value, user_id=user_id)
    except TrainingPlan.DoesNotExist as exc:
        raise ValueError("Training plan was not found.") from exc


def _get_exercise(exercise_value: Exercise | str, *, user_id: str) -> Exercise:
    if isinstance(exercise_value, Exercise):
        if exercise_value.user_id not in (user_id, ""):
            raise ValueError("Exercise was not found.")
        return exercise_value

    try:
        return Exercise.objects.get(Q(user_id=user_id) | Q(user_id=""), pk=exercise_value)
    except Exercise.DoesNotExist as exc:
        raise ValueError("Exercise was not found.") from exc


def _version_from_workout(workout: Workout) -> str:
    return workout.updated_at.isoformat()
