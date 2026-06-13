from django.test import TestCase

from training import services
from training.models import Exercise


class ExerciseServiceTests(TestCase):
    user_id = "user-1"

    def test_create_exercise(self) -> None:
        starting_count = Exercise.objects.count()
        exercise = services.create_exercise(
            {
                "name": "Push-Up",
                "default_sets": 3,
                "default_reps": 12,
                "muscle_group": "Chest",
                "default_time": 0,
                "notes": "Keep core tight.",
            },
            user_id=self.user_id,
        )
        self.assertEqual(exercise.name, "Push-Up")
        self.assertEqual(exercise.user_id, self.user_id)
        self.assertEqual(exercise.default_sets, 3)
        self.assertEqual(exercise.default_reps, 12)
        self.assertEqual(exercise.muscle_group, "Chest")
        self.assertEqual(exercise.default_time, 0)
        self.assertEqual(exercise.notes, "Keep core tight.")
        self.assertEqual(Exercise.objects.count(), starting_count + 1)

    def test_update_exercise_defaults(self) -> None:
        exercise = services.create_exercise(
            {"name": "Plank", "prescription_type": "timed"},
            user_id=self.user_id,
        )
        updated = services.update_exercise(
            exercise,
            {"default_sets": 4, "default_reps": 10, "default_time": 2},
            user_id=self.user_id,
        )
        self.assertEqual(updated.default_sets, 4)
        self.assertEqual(updated.default_reps, 10)
        self.assertEqual(updated.default_time, 2)
