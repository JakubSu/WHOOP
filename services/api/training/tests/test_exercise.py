from django.test import TestCase

from training import services
from training.models import Exercise


class ExerciseServiceTests(TestCase):
    def test_create_exercise(self) -> None:
        starting_count = Exercise.objects.count()
        exercise = services.create_exercise({"name": "Push-Up", "category": Exercise.Category.STRENGTH})
        self.assertEqual(exercise.name, "Push-Up")
        self.assertEqual(Exercise.objects.count(), starting_count + 1)

    def test_favorite_clears_avoided(self) -> None:
        exercise = services.create_exercise({"name": "Push-Up", "is_avoided": True})
        updated = services.update_exercise(exercise, {"is_favorite": True})
        self.assertTrue(updated.is_favorite)
        self.assertFalse(updated.is_avoided)

    def test_invalid_preference_combination_raises(self) -> None:
        with self.assertRaises(ValueError):
            services.create_exercise({"name": "Push-Up", "is_favorite": True, "is_avoided": True})
