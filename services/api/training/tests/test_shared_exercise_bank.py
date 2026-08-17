from django.test import TestCase

from training.models import Exercise
from training.services.shared_exercise_bank import sync_shared_exercise_bank


class SharedExerciseBankSyncTests(TestCase):
    def test_sync_recreates_missing_shared_exercises_without_touching_user_exercises(
        self,
    ) -> None:
        Exercise.objects.get(user_id="", name="Pull-Up").delete()
        personal = Exercise.objects.create(
            user_id="user-1",
            name="Pull-Up",
            default_sets=9,
            default_reps=9,
            notes="Personal default.",
        )

        result = sync_shared_exercise_bank()

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.unchanged, 44)
        self.assertTrue(Exercise.objects.filter(user_id="", name="Pull-Up").exists())
        personal.refresh_from_db()
        self.assertEqual(personal.default_sets, 9)
        self.assertEqual(personal.notes, "Personal default.")
