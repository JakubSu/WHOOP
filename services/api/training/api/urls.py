from django.urls import path

from training.api.views import (
    ExerciseCollectionAPIView,
    ExerciseDetailAPIView,
    TrainingPlanCollectionAPIView,
    TrainingPlanDetailAPIView,
    WorkoutCollectionAPIView,
    WorkoutDetailAPIView,
    WorkoutExerciseCollectionAPIView,
    WorkoutExerciseDetailAPIView,
    WorkoutSnapshotCollectionAPIView,
    WorkoutSnapshotDetailAPIView,
)


urlpatterns = [
    path("exercises/", ExerciseCollectionAPIView.as_view(), name="exercise-collection"),
    path("exercises/<uuid:pk>/", ExerciseDetailAPIView.as_view(), name="exercise-detail"),
    path("training-plans/", TrainingPlanCollectionAPIView.as_view(), name="training-plan-collection"),
    path("training-plans/<uuid:pk>/", TrainingPlanDetailAPIView.as_view(), name="training-plan-detail"),
    path("workouts/", WorkoutCollectionAPIView.as_view(), name="workout-collection"),
    path("workouts/<uuid:pk>/", WorkoutDetailAPIView.as_view(), name="workout-detail"),
    path("workout-snapshots/", WorkoutSnapshotCollectionAPIView.as_view(), name="workout-snapshot-collection"),
    path("workout-snapshots/<uuid:pk>/", WorkoutSnapshotDetailAPIView.as_view(), name="workout-snapshot-detail"),
    path("workout-exercises/", WorkoutExerciseCollectionAPIView.as_view(), name="workout-exercise-collection"),
    path("workout-exercises/<uuid:pk>/", WorkoutExerciseDetailAPIView.as_view(), name="workout-exercise-detail"),
]
