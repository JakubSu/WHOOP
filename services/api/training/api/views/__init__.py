from training.api.views.exercise import ExerciseCollectionAPIView, ExerciseDetailAPIView
from training.api.views.training_plan import (
    TrainingPlanCollectionAPIView,
    TrainingPlanDetailAPIView,
    TrainingPlanWorkoutCollectionAPIView,
)
from training.api.views.workout import (
    WorkoutCollectionAPIView,
    WorkoutDetailAPIView,
    WorkoutExercisePageCollectionAPIView,
)
from training.api.views.workout_exercise import WorkoutExerciseCollectionAPIView, WorkoutExerciseDetailAPIView

__all__ = [
    "ExerciseCollectionAPIView",
    "ExerciseDetailAPIView",
    "TrainingPlanCollectionAPIView",
    "TrainingPlanDetailAPIView",
    "TrainingPlanWorkoutCollectionAPIView",
    "WorkoutCollectionAPIView",
    "WorkoutDetailAPIView",
    "WorkoutExercisePageCollectionAPIView",
    "WorkoutExerciseCollectionAPIView",
    "WorkoutExerciseDetailAPIView",
]
