from typing import Any

from django.db.models import Q

from training.models import Exercise


def list_exercises(
    user_id: str, *, muscle_group: Exercise.MuscleGroup | None = None
) -> list[Exercise]:
    exercises = Exercise.objects.filter(Q(user_id=user_id) | Q(user_id=""))
    if muscle_group is not None:
        exercises = exercises.filter(muscle_group=muscle_group)
    return list(exercises)


def get_exercise(exercise_id: str, user_id: str) -> Exercise | None:
    try:
        return Exercise.objects.get(Q(user_id=user_id) | Q(user_id=""), pk=exercise_id)
    except Exercise.DoesNotExist:
        return None


def create_exercise(data: dict[str, Any], *, user_id: str) -> Exercise:
    payload = _normalized_payload(data)
    payload["user_id"] = user_id
    return Exercise.objects.create(**payload)


def update_exercise(
    exercise: Exercise, data: dict[str, Any], *, user_id: str
) -> Exercise:
    if exercise.user_id != user_id:
        raise ValueError("Exercise was not found.")
    payload = _normalized_payload(data, existing=exercise)
    for field, value in payload.items():
        setattr(exercise, field, value)
    exercise.save()
    return exercise


def delete_exercise(exercise: Exercise, *, user_id: str) -> None:
    if exercise.user_id != user_id:
        raise ValueError("Exercise was not found.")
    exercise.delete()


def _normalized_payload(
    data: dict[str, Any], existing: Exercise | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    fields = (
        "name",
        "prescription_type",
        "default_sets",
        "default_reps",
        "default_weight",
        "default_weight_unit",
        "muscle_group",
        "default_time",
        "notes",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    _validate_exercise_defaults(payload)
    return payload


def _validate_exercise_defaults(payload: dict[str, Any]) -> None:
    prescription_type = payload.get(
        "prescription_type", Exercise.PrescriptionType.STRENGTH
    )
    if prescription_type == Exercise.PrescriptionType.TIMED:
        return
    if payload.get("default_time", 0) > 0:
        raise ValueError("Strength exercises cannot use a default time.")
