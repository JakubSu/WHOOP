from django.test import TestCase
from decimal import Decimal

from training import services
from training.models import WorkoutExercise


class WorkoutExerciseServiceTests(TestCase):
    user_id = "user-1"

    def test_create_workout_exercise(self) -> None:
        workout = services.create_workout({"name": "Upper Body"}, user_id=self.user_id)
        exercise = services.create_exercise(
            {"name": "Push-Up"},
            user_id=self.user_id,
        )

        workout_exercise = services.create_workout_exercise(
            {
                "workout": str(workout.id),
                "exercise": str(exercise.id),
                "sets": 3,
                "reps": 12,
                "weight": "45.50",
                "weight_unit": "lb",
                "note": "Clean reps.",
            },
            user_id=self.user_id,
        )

        self.assertEqual(workout_exercise.workout, workout)
        self.assertEqual(workout_exercise.exercise, exercise)
        workout_exercise.refresh_from_db()
        self.assertEqual(workout_exercise.sets, 3)
        self.assertEqual(workout_exercise.reps, 12)
        self.assertEqual(workout_exercise.weight, Decimal("45.50"))
        self.assertEqual(workout_exercise.weight_unit, "lb")
        self.assertEqual(workout_exercise.note, "Clean reps.")
        self.assertTrue(WorkoutExercise.objects.filter(pk=workout_exercise.id).exists())

    def test_strength_workout_exercise_rejects_time(self) -> None:
        workout = services.create_workout({"name": "Upper Body"}, user_id=self.user_id)
        exercise = services.create_exercise({"name": "Push-Up"}, user_id=self.user_id)

        with self.assertRaises(ValueError):
            services.create_workout_exercise(
                {
                    "workout": str(workout.id),
                    "exercise": str(exercise.id),
                    "sets": 3,
                    "reps": 12,
                    "time": 30,
                },
                user_id=self.user_id,
            )

    def test_timed_workout_exercise_accepts_time(self) -> None:
        workout = services.create_workout({"name": "Core"}, user_id=self.user_id)
        exercise = services.create_exercise(
            {"name": "Plank", "prescription_type": "timed", "default_time": 45},
            user_id=self.user_id,
        )

        workout_exercise = services.create_workout_exercise(
            {
                "workout": str(workout.id),
                "exercise": str(exercise.id),
                "time": 45,
            },
            user_id=self.user_id,
        )

        self.assertEqual(workout_exercise.time, 45)

    def test_create_workout_with_training_plan(self) -> None:
        training_plan = services.create_training_plan({"name": "Strength Block"}, user_id=self.user_id)
        workout = services.create_workout(
            {
                "name": "Lower Body",
                "plan": str(training_plan.id),
                "date": "2026-06-10",
            },
            user_id=self.user_id,
        )

        self.assertEqual(workout.plan, training_plan)
