from django.urls import path

from training.api.views import (
    ExerciseCollectionAPIView,
    ExerciseDetailAPIView,
    WorkoutCollectionAPIView,
    WorkoutDetailAPIView,
    WorkoutExercisePageCollectionAPIView,
    WorkoutExercisePageDetailAPIView,
    WorkoutLandingAPIView,
)

urlpatterns = [
    path("exercises/", ExerciseCollectionAPIView.as_view(), name="exercise-collection"),
    path("exercises/<uuid:pk>/", ExerciseDetailAPIView.as_view(), name="exercise-detail"),
    path("workouts/landing/", WorkoutLandingAPIView.as_view(), name="workout-landing"),
    path("workouts/", WorkoutCollectionAPIView.as_view(), name="workout-collection"),
    path("workouts/<uuid:pk>/", WorkoutDetailAPIView.as_view(), name="workout-detail"),
    path("workouts/<uuid:pk>/exercises/", WorkoutExercisePageCollectionAPIView.as_view(), name="workout-exercise-page-collection"),
    path("workouts/<uuid:pk>/exercises/<uuid:workout_exercise_id>/", WorkoutExercisePageDetailAPIView.as_view(), name="workout-exercise-page-detail"),
]

# Training-plan endpoints are intentionally disabled while the public API is
# workout-first. Keep the implementation in place so plan screens can be
# re-enabled without rebuilding the plan bounded context.
#
# from training.api.views.training_plan import (
#     TrainingPlanCollectionAPIView,
#     TrainingPlanDetailAPIView,
#     TrainingPlanWorkoutCollectionAPIView,
# )
#
# urlpatterns += [
#     path("training-plans/", TrainingPlanCollectionAPIView.as_view(), name="training-plan-collection"),
#     path("training-plans/<uuid:pk>/", TrainingPlanDetailAPIView.as_view(), name="training-plan-detail"),
#     path("training-plans/<uuid:pk>/workouts/", TrainingPlanWorkoutCollectionAPIView.as_view(), name="training-plan-workout-collection"),
# ]
