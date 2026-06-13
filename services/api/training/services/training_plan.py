from typing import Any

from django.db.models import Count

from training.models import TrainingPlan, Workout


def list_training_plans(user_id: str) -> list[TrainingPlan]:
    return list(TrainingPlan.objects.filter(user_id=user_id))


def get_training_plan(training_plan_id: str, user_id: str) -> TrainingPlan | None:
    try:
        return TrainingPlan.objects.get(pk=training_plan_id, user_id=user_id)
    except TrainingPlan.DoesNotExist:
        return None


def list_plan_workouts(training_plan_id: str, user_id: str) -> list[Workout]:
    return list(
        Workout.objects.filter(plan_id=training_plan_id, user_id=user_id)
        .annotate(exercise_count=Count("workout_exercises"))
        .order_by("-date", "name")
    )


def create_training_plan(data: dict[str, Any], *, user_id: str) -> TrainingPlan:
    payload = _normalized_training_plan_payload(data)
    payload["user_id"] = user_id
    return TrainingPlan.objects.create(**payload)


def update_training_plan(training_plan: TrainingPlan, data: dict[str, Any]) -> TrainingPlan:
    payload = _normalized_training_plan_payload(data, existing=training_plan)
    for field, value in payload.items():
        setattr(training_plan, field, value)
    training_plan.save()
    return training_plan


def delete_training_plan(training_plan: TrainingPlan) -> None:
    training_plan.delete()


def _normalized_training_plan_payload(
    data: dict[str, Any],
    existing: TrainingPlan | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    fields = (
        "name",
        "start_date",
        "end_date",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    return payload
