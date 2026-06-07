from django.test import TestCase

from training import services
from training.models import Exercise, Workout, WorkoutExercise


class WorkoutExerciseServiceTests(TestCase):
    def test_create_workout_exercise(self) -> None:
        workout = services.create_workout({"name": "Upper Body"})
        exercise = services.create_exercise({"name": "Push-Up", "category": Exercise.Category.STRENGTH})

        workout_exercise = services.create_workout_exercise(
            {
                "workout": str(workout.id),
                "exercise": str(exercise.id),
                "position": 1,
                "sets": 3,
                "reps": 12,
            }
        )

        self.assertEqual(workout_exercise.workout, workout)
        self.assertEqual(workout_exercise.exercise, exercise)
        self.assertEqual(WorkoutExercise.objects.count(), 1)

    def test_create_workout_with_training_plan(self) -> None:
        training_plan = services.create_training_plan({"name": "Strength Block"})
        workout = services.create_workout({"name": "Lower Body", "training_plan": str(training_plan.id)})

        self.assertEqual(workout.training_plan, training_plan)
        self.assertEqual(workout.status, Workout.Status.PLANNED)
