from typing import Any

from django.db.models import Q

from training.models import Exercise


def list_exercises(user_id: str) -> list[Exercise]:
    return list(Exercise.objects.filter(Q(user_id=user_id) | Q(user_id="")))


def get_exercise(exercise_id: str, user_id: str) -> Exercise | None:
    try:
        return Exercise.objects.get(Q(user_id=user_id) | Q(user_id=""), pk=exercise_id)
    except Exercise.DoesNotExist:
        return None


def create_exercise(data: dict[str, Any], *, user_id: str) -> Exercise:
    payload = _normalized_payload(data)
    payload["user_id"] = user_id
    return Exercise.objects.create(**payload)


def update_exercise(exercise: Exercise, data: dict[str, Any], *, user_id: str) -> Exercise:
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


def _normalized_payload(data: dict[str, Any], existing: Exercise | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    fields = (
        "name",
        "category",
        "primary_muscle_group",
        "secondary_muscle_groups",
        "equipment",
        "default_intensity",
        "notes",
        "default_sets",
        "default_reps",
        "is_favorite",
        "is_avoided",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    favorite_explicit = "is_favorite" in data
    avoided_explicit = "is_avoided" in data

    if favorite_explicit and avoided_explicit and data.get("is_favorite") and data.get("is_avoided"):
        raise ValueError("Exercise cannot be marked favorite and avoided at the same time.")
    if favorite_explicit and data.get("is_favorite"):
        payload["is_avoided"] = False
    elif avoided_explicit and data.get("is_avoided"):
        payload["is_favorite"] = False

    return payload
