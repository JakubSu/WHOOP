from typing import Any

from training.models import Exercise


def list_exercises() -> list[Exercise]:
    return list(Exercise.objects.all())


def get_exercise(exercise_id: str) -> Exercise | None:
    try:
        return Exercise.objects.get(pk=exercise_id)
    except Exercise.DoesNotExist:
        return None


def create_exercise(data: dict[str, Any]) -> Exercise:
    payload = _normalized_payload(data)
    return Exercise.objects.create(**payload)


def update_exercise(exercise: Exercise, data: dict[str, Any]) -> Exercise:
    payload = _normalized_payload(data, existing=exercise)
    for field, value in payload.items():
        setattr(exercise, field, value)
    exercise.save()
    return exercise


def delete_exercise(exercise: Exercise) -> None:
    exercise.delete()


def _normalized_payload(data: dict[str, Any], existing: Exercise | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    fields = (
        "user_id",
        "name",
        "category",
        "primary_muscle_group",
        "equipment",
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
