from django.test import TestCase

from training import services
from training.models import Exercise, Workout, WorkoutExercise


class WorkoutExerciseServiceTests(TestCase):
    user_id = "user-1"

    def test_create_workout_exercise(self) -> None:
        workout = services.create_workout({"name": "Upper Body"}, user_id=self.user_id)
        exercise = services.create_exercise(
            {"name": "Push-Up", "category": Exercise.Category.STRENGTH},
            user_id=self.user_id,
        )

        workout_exercise = services.create_workout_exercise(
            {
                "workout": str(workout.id),
                "exercise": str(exercise.id),
                "position": 1,
                "sets": 3,
                "reps": 12,
            },
            user_id=self.user_id,
        )

        self.assertEqual(workout_exercise.workout, workout)
        self.assertEqual(workout_exercise.exercise, exercise)
        self.assertEqual(WorkoutExercise.objects.count(), 1)

    def test_create_workout_with_training_plan(self) -> None:
        training_plan = services.create_training_plan({"name": "Strength Block"}, user_id=self.user_id)
        workout = services.create_workout(
            {"name": "Lower Body", "training_plan": str(training_plan.id)},
            user_id=self.user_id,
        )

        self.assertEqual(workout.training_plan, training_plan)
        self.assertEqual(workout.status, Workout.Status.PLANNED)
