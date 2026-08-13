"""User-scoped training workout tools."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from ai.tools.context import CoachToolContext
from ai.tools.contracts import WorkoutDetail, WorkoutExerciseDetail, WorkoutSummary
from ai.tools.errors import ToolNotFoundError
from training.models import Workout

MAX_WORKOUT_RESULTS = 100


def search_workouts(
    context: CoachToolContext,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 20,
) -> list[WorkoutSummary]:
    """Returns a bounded date-ordered list of workouts owned by the active user."""

    queryset = Workout.objects.filter(user_id=str(context.user.id))
    if start_date is not None:
        queryset = queryset.filter(date__gte=start_date)
    if end_date is not None:
        queryset = queryset.filter(date__lte=end_date)
    return [
        WorkoutSummary(
            id=workout.id,
            name=workout.name,
            date=workout.date,
            expected_time=workout.expected_time,
        )
        for workout in queryset.order_by("date", "id")[
            : max(1, min(limit, MAX_WORKOUT_RESULTS))
        ]
    ]


def get_workout(context: CoachToolContext, *, workout_id: UUID) -> WorkoutDetail:
    """Returns one active-user workout and its ordered exercise prescriptions."""

    workout = (
        Workout.objects.filter(pk=workout_id, user_id=str(context.user.id))
        .prefetch_related("workout_exercises__exercise")
        .first()
    )
    if workout is None:
        raise ToolNotFoundError("Workout was not found.")
    return WorkoutDetail(
        id=workout.id,
        name=workout.name,
        date=workout.date,
        expected_time=workout.expected_time,
        exercises=[
            WorkoutExerciseDetail(
                workout_exercise_id=item.id,
                exercise_id=item.exercise_id,
                name=item.exercise.name,
                position=item.sort_order,
                sets=item.sets,
                reps=item.reps,
                time=item.time,
                weight=float(item.weight) if item.weight is not None else None,
                weight_unit=item.weight_unit,
                note=item.note,
            )
            for item in workout.workout_exercises.all()
        ],
    )
