from datetime import date
from typing import Any

from django.db.models import Count, QuerySet

from recommendation.services.invalidation import (
    stale_pending_recommendation_operations_for_workout,
    stale_pending_recommendation_operations_for_workout_exercise,
)
from training.domain import WorkoutLanding
from training.models import TrainingPlan, Workout


def list_workouts(
    user_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Workout]:
    return list(
        _workout_list_queryset(
            user_id,
            start_date=start_date,
            end_date=end_date,
        )
    )


def list_workouts_page(
    user_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[int, list[Workout]]:
    queryset = _workout_list_queryset(
        user_id,
        start_date=start_date,
        end_date=end_date,
    )
    count = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return count, list(queryset[start:end])


def get_workout(workout_id: str, user_id: str) -> Workout | None:
    try:
        return Workout.objects.annotate(exercise_count=Count("workout_exercises")).get(
            pk=workout_id, user_id=user_id
        )
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
    stale_pending_recommendation_operations_for_workout(workout_id=str(workout.id))
    for field, value in payload.items():
        setattr(workout, field, value)
    workout.save()
    return workout


def delete_workout(workout: Workout) -> None:
    stale_pending_recommendation_operations_for_workout(workout_id=str(workout.id))
    for workout_exercise_id in workout.workout_exercises.values_list("id", flat=True):
        stale_pending_recommendation_operations_for_workout_exercise(
            workout_exercise_id=str(workout_exercise_id)
        )
    workout.delete()


def _workout_list_queryset(
    user_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> QuerySet[Workout]:
    queryset = Workout.objects.filter(user_id=user_id).annotate(
        exercise_count=Count("workout_exercises")
    )
    if start_date is not None:
        queryset = queryset.filter(date__gte=start_date)
    if end_date is not None:
        queryset = queryset.filter(date__lte=end_date)
    return queryset.order_by("date", "name", "id")


def get_workout_landing(user_id: str, today_value: str | date) -> WorkoutLanding | None:
    """Select from every scheduled workout for the user.

    Training plans are a legacy grouping and must not affect the workout shown
    on the landing screen.
    """
    today = _coerce_date(today_value)
    workouts = list(
        Workout.objects.filter(user_id=user_id).order_by("date", "name")
    )
    if not workouts:
        return None

    todays_workout = next(
        (workout for workout in workouts if workout.date == today), None
    )
    if todays_workout is not None:
        return WorkoutLanding(
            workout=todays_workout,
            is_today=True,
            has_workout_today=True,
            message=None,
        )

    upcoming_workout = next(
        (workout for workout in workouts if workout.date > today), None
    )
    if upcoming_workout is None:
        return WorkoutLanding(
            workout=workouts[-1],
            is_today=False,
            has_workout_today=False,
            message="No workout scheduled today",
        )

    return WorkoutLanding(
        workout=upcoming_workout,
        is_today=False,
        has_workout_today=False,
        message="No workout scheduled today",
    )


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

    if payload.get("date") is None:
        raise ValueError("Workout date is required.")

    return payload


def _get_training_plan(
    training_plan_value: TrainingPlan | str | None, *, user_id: str
) -> TrainingPlan | None:
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


def _coerce_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
