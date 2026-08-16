"""Framework-independent read and write tools available to coach AI adapters."""

from ai.tools.context import CoachToolContext
from ai.tools.exercises import get_exercise, search_exercises
from ai.tools.recommendations import create_recommendation, get_active_recommendation
from ai.tools.recovery import get_whoop_summary
from ai.tools.workouts import get_workout, search_workouts

__all__ = [
    "CoachToolContext",
    "create_recommendation",
    "get_active_recommendation",
    "get_exercise",
    "get_whoop_summary",
    "get_workout",
    "search_exercises",
    "search_workouts",
]
