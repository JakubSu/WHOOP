"""Safe result contracts returned by framework-independent AI tools."""

from ai.tools.contracts.exercises import ExerciseSummary
from ai.tools.contracts.recommendations import (
    ActiveRecommendation,
    CreatedRecommendation,
)
from ai.tools.contracts.recovery import WhoopSummary
from ai.tools.contracts.workouts import (
    WorkoutDetail,
    WorkoutExerciseDetail,
    WorkoutSummary,
)

__all__ = [
    "ActiveRecommendation",
    "CreatedRecommendation",
    "ExerciseSummary",
    "WhoopSummary",
    "WorkoutDetail",
    "WorkoutExerciseDetail",
    "WorkoutSummary",
]
