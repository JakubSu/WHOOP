from typing import Any

from training.models import TrainingPlan


def list_training_plans() -> list[TrainingPlan]:
    return list(TrainingPlan.objects.all())


def get_training_plan(training_plan_id: str) -> TrainingPlan | None:
    try:
        return TrainingPlan.objects.get(pk=training_plan_id)
    except TrainingPlan.DoesNotExist:
        return None


def create_training_plan(data: dict[str, Any]) -> TrainingPlan:
    payload = _normalized_training_plan_payload(data)
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
        "user_id",
        "name",
        "goal",
        "start_date",
        "end_date",
        "status",
        "notes",
    )

    for field in fields:
        if field in data:
            payload[field] = data[field]
        elif existing is not None:
            payload[field] = getattr(existing, field)

    return payload
