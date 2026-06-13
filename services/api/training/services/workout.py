from typing import Any

from training.models import TrainingPlan, Workout


def list_workouts(user_id: str) -> list[Workout]:
    return list(Workout.objects.filter(user_id=user_id))


def get_workout(workout_id: str, user_id: str) -> Workout | None:
    try:
        return Workout.objects.get(pk=workout_id, user_id=user_id)
    except Workout.DoesNotExist:
        return None


def create_workout(data: dict[str, Any], *, user_id: str) -> Workout:
    payload = _normalized_workout_payload(data, user_id=user_id)
    payload["user_id"] = user_id
    return Workout.objects.create(**payload)


def update_workout(workout: Workout, data: dict[str, Any], *, user_id: str) -> Workout:
    if workout.user_id != user_id:
        raise ValueError("Workout was not found.")
    payload = _normalized_workout_payload(data, existing=workout, user_id=user_id)
    for field, value in payload.items():
        setattr(workout, field, value)
    workout.save()
    return workout


def delete_workout(workout: Workout) -> None:
    workout.delete()


def _normalized_workout_payload(
    data: dict[str, Any],
    existing: Workout | None = None,
    *,
    user_id: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if "plan" in data:
        payload["plan"] = _get_training_plan(data["plan"], user_id=user_id)
    elif existing is not None:
        payload["plan"] = existing.plan

    fields = (
        "name",
        "date",
        "expected_time",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    return payload


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
