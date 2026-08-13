"""User-scoped and shared exercise-library tools."""

from __future__ import annotations

from django.db.models import Q

from ai.tools.context import CoachToolContext
from ai.tools.contracts import ExerciseSummary
from ai.tools.errors import ToolValidationError
from training.models import Exercise

MAX_EXERCISE_RESULTS = 200
MAX_EXERCISE_QUERY_LENGTH = 100
MAX_MUSCLE_GROUP_FILTERS = len(Exercise.MuscleGroup.values)


def search_exercises(
    context: CoachToolContext,
    *,
    names: list[str] | None = None,
    muscle_groups: list[Exercise.MuscleGroup] | None = None,
    limit: int = 50,
) -> list[ExerciseSummary]:
    """Searches user and shared exercises by optional names and muscle groups."""

    requested_names = [
        name.strip()[:MAX_EXERCISE_QUERY_LENGTH] for name in names or [] if name.strip()
    ]
    groups = muscle_groups or []
    if len(groups) > MAX_MUSCLE_GROUP_FILTERS or len(set(groups)) != len(groups):
        raise ToolValidationError("Exercise filters could not be applied.")

    exercises = Exercise.objects.filter(user_id__in=[str(context.user.id), ""])
    if requested_names:
        name_filter = Q()
        for name in requested_names:
            name_filter |= Q(name__icontains=name)
        exercises = exercises.filter(name_filter)
    if groups:
        exercises = exercises.filter(muscle_group__in=groups)
    return [
        ExerciseSummary(
            id=exercise.id,
            name=exercise.name,
            prescription_type=exercise.prescription_type,
            muscle_group=exercise.muscle_group,
        )
        for exercise in exercises.order_by("name", "id")[
            : max(1, min(limit, MAX_EXERCISE_RESULTS))
        ]
    ]
