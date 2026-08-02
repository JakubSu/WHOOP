from training.api.views.exercise import ExerciseCollectionAPIView, ExerciseDetailAPIView
from training.api.views.workout import (
    WorkoutCollectionAPIView,
    WorkoutDetailAPIView,
    WorkoutLandingAPIView,
)
from training.api.views.workout_exercise import (
    WorkoutExercisePageCollectionAPIView,
    WorkoutExercisePageDetailAPIView,
)

__all__ = [
    "ExerciseCollectionAPIView",
    "ExerciseDetailAPIView",
    "WorkoutCollectionAPIView",
    "WorkoutDetailAPIView",
    "WorkoutExercisePageCollectionAPIView",
    "WorkoutExercisePageDetailAPIView",
    "WorkoutLandingAPIView",
]
