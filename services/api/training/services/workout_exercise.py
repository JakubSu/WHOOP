from typing import Any

from django.db.models import Q

from training.models import Exercise, Workout, WorkoutExercise


def list_workout_exercises(user_id: str) -> list[WorkoutExercise]:
    return list(WorkoutExercise.objects.select_related("workout", "exercise").filter(workout__user_id=user_id))


def get_workout_exercise(workout_exercise_id: str, user_id: str) -> WorkoutExercise | None:
    try:
        return WorkoutExercise.objects.select_related("workout", "exercise").get(pk=workout_exercise_id, workout__user_id=user_id)
    except WorkoutExercise.DoesNotExist:
        return None


def list_workout_exercises_for_workout(workout_id: str, user_id: str) -> list[WorkoutExercise]:
    return list(
        WorkoutExercise.objects.select_related("workout", "exercise")
        .filter(workout_id=workout_id, workout__user_id=user_id)
        .order_by("created_at", "exercise__name")
    )


def create_workout_exercise(data: dict[str, Any], *, user_id: str) -> WorkoutExercise:
    payload = _normalized_workout_exercise_payload(data, user_id=user_id)
    return WorkoutExercise.objects.create(**payload)


def update_workout_exercise(workout_exercise: WorkoutExercise, data: dict[str, Any], *, user_id: str) -> WorkoutExercise:
    if workout_exercise.workout.user_id != user_id:
        raise ValueError("Workout exercise was not found.")
    payload = _normalized_workout_exercise_payload(data, existing=workout_exercise, user_id=user_id)
    for field, value in payload.items():
        setattr(workout_exercise, field, value)
    workout_exercise.save()
    return workout_exercise


def delete_workout_exercise(workout_exercise: WorkoutExercise, *, user_id: str) -> None:
    if workout_exercise.workout.user_id != user_id:
        raise ValueError("Workout exercise was not found.")
    workout_exercise.delete()


def _normalized_workout_exercise_payload(
    data: dict[str, Any],
    existing: WorkoutExercise | None = None,
    *,
    user_id: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "workout" in data:
        payload["workout"] = _get_workout(data["workout"], user_id=user_id)
    elif existing is not None:
        payload["workout"] = existing.workout

    if "exercise" in data:
        payload["exercise"] = _get_exercise(data["exercise"], user_id=user_id)
    elif existing is not None:
        payload["exercise"] = existing.exercise

    fields = (
        "sets",
        "reps",
        "time",
        "weight",
        "weight_unit",
        "note",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    if "weight_unit" not in payload:
        payload["weight_unit"] = "lb"

    _validate_workout_exercise_prescription(payload)
    return payload


def _validate_workout_exercise_prescription(payload: dict[str, Any]) -> None:
    exercise = payload.get("exercise")
    if exercise is None:
        return

    prescription_type = exercise.prescription_type
    if prescription_type == Exercise.PrescriptionType.TIMED:
        if payload.get("sets", 0) > 0 or payload.get("reps", 0) > 0 or payload.get("weight") is not None:
            raise ValueError("Timed exercises can only use time and note.")
        return

    if payload.get("time", 0) > 0:
        raise ValueError("Strength exercises can only use sets, reps, weight, and note.")


def _get_workout(workout_value: Workout | str, *, user_id: str) -> Workout:
    if isinstance(workout_value, Workout):
        if workout_value.user_id != user_id:
            raise ValueError("Workout was not found.")
        return workout_value

    try:
        return Workout.objects.get(pk=workout_value, user_id=user_id)
    except Workout.DoesNotExist as exc:
        raise ValueError("Workout was not found.") from exc


def _get_exercise(exercise_value: Exercise | str, *, user_id: str) -> Exercise:
    if isinstance(exercise_value, Exercise):
        if exercise_value.user_id not in (user_id, ""):
            raise ValueError("Exercise was not found.")
        return exercise_value

    try:
        return Exercise.objects.get(Q(user_id=user_id) | Q(user_id=""), pk=exercise_value)
    except Exercise.DoesNotExist as exc:
        raise ValueError("Exercise was not found.") from exc
