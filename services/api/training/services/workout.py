from typing import Any

from django.utils import timezone

from training.models import TrainingPlan, Workout


def list_workouts() -> list[Workout]:
    return list(Workout.objects.all())


def get_workout(workout_id: str) -> Workout | None:
    try:
        return Workout.objects.get(pk=workout_id)
    except Workout.DoesNotExist:
        return None


def create_workout(data: dict[str, Any]) -> Workout:
    payload = _normalized_workout_payload(data)
    return Workout.objects.create(**payload)


def update_workout(workout: Workout, data: dict[str, Any]) -> Workout:
    payload = _normalized_workout_payload(data, existing=workout)
    for field, value in payload.items():
        setattr(workout, field, value)
    workout.save()
    return workout


def delete_workout(workout: Workout) -> None:
    workout.delete()


def _normalized_workout_payload(data: dict[str, Any], existing: Workout | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if "training_plan" in data:
        payload["training_plan"] = _get_training_plan(data["training_plan"])
    elif existing is not None:
        payload["training_plan"] = existing.training_plan

    fields = (
        "user_id",
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

    if "status" not in payload:
        payload["status"] = Workout.Status.PLANNED

    if payload.get("status") == Workout.Status.COMPLETED and payload.get("completed_at") is None:
        payload["completed_at"] = timezone.now()

    return payload


def _get_training_plan(training_plan_value: TrainingPlan | str | None) -> TrainingPlan | None:
    if not training_plan_value:
        return None

    if isinstance(training_plan_value, TrainingPlan):
        return training_plan_value

    try:
        return TrainingPlan.objects.get(pk=training_plan_value)
    except TrainingPlan.DoesNotExist as exc:
        raise ValueError("Training plan was not found.") from exc
