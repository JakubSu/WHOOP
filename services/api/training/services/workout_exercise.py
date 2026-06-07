from typing import Any

from training.models import Exercise, Workout, WorkoutExercise


def list_workout_exercises() -> list[WorkoutExercise]:
    return list(WorkoutExercise.objects.select_related("workout", "exercise").all())


def get_workout_exercise(workout_exercise_id: str) -> WorkoutExercise | None:
    try:
        return WorkoutExercise.objects.select_related("workout", "exercise").get(pk=workout_exercise_id)
    except WorkoutExercise.DoesNotExist:
        return None


def create_workout_exercise(data: dict[str, Any]) -> WorkoutExercise:
    payload = _normalized_workout_exercise_payload(data)
    return WorkoutExercise.objects.create(**payload)


def update_workout_exercise(workout_exercise: WorkoutExercise, data: dict[str, Any]) -> WorkoutExercise:
    payload = _normalized_workout_exercise_payload(data, existing=workout_exercise)
    for field, value in payload.items():
        setattr(workout_exercise, field, value)
    workout_exercise.save()
    return workout_exercise


def delete_workout_exercise(workout_exercise: WorkoutExercise) -> None:
    workout_exercise.delete()


def _normalized_workout_exercise_payload(
    data: dict[str, Any],
    existing: WorkoutExercise | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "workout" in data:
        payload["workout"] = _get_workout(data["workout"])
    elif existing is not None:
        payload["workout"] = existing.workout

    if "exercise" in data:
        payload["exercise"] = _get_exercise(data["exercise"])
    elif existing is not None:
        payload["exercise"] = existing.exercise

    fields = (
        "position",
        "sets",
        "reps",
        "duration_seconds",
        "load",
        "rest_seconds",
        "notes",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    return payload


def _get_workout(workout_value: Workout | str) -> Workout:
    if isinstance(workout_value, Workout):
        return workout_value

    try:
        return Workout.objects.get(pk=workout_value)
    except Workout.DoesNotExist as exc:
        raise ValueError("Workout was not found.") from exc


def _get_exercise(exercise_value: Exercise | str) -> Exercise:
    if isinstance(exercise_value, Exercise):
        return exercise_value

    try:
        return Exercise.objects.get(pk=exercise_value)
    except Exercise.DoesNotExist as exc:
        raise ValueError("Exercise was not found.") from exc
