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
                "default_weight": "135.00",
                "default_weight_unit": "kg",
                "muscle_group": Exercise.MuscleGroup.CHEST,
                "default_time": 0,
                "notes": "Keep core tight.",
            },
            user_id=self.user_id,
        )
        self.assertEqual(exercise.name, "Push-Up")
        self.assertEqual(exercise.user_id, self.user_id)
        self.assertEqual(exercise.default_sets, 3)
        self.assertEqual(exercise.default_reps, 12)
        self.assertEqual(str(exercise.default_weight), "135.00")
        self.assertEqual(exercise.default_weight_unit, "kg")
        self.assertEqual(exercise.muscle_group, Exercise.MuscleGroup.CHEST)
        self.assertEqual(exercise.default_time, 0)
        self.assertEqual(exercise.notes, "Keep core tight.")
        self.assertEqual(Exercise.objects.count(), starting_count + 1)

    def test_create_exercise_defaults_to_other_muscle_group(self) -> None:
        """Exercises always receive a valid primary muscle-group value."""

        exercise = services.create_exercise({"name": "Carry"}, user_id=self.user_id)

        self.assertEqual(exercise.muscle_group, Exercise.MuscleGroup.OTHER)

    def test_update_exercise_defaults(self) -> None:
        exercise = services.create_exercise(
            {"name": "Intervals", "prescription_type": "timed_sets"},
            user_id=self.user_id,
        )
        updated = services.update_exercise(
            exercise,
            {
                "default_sets": 4,
                "default_time": 2,
            },
            user_id=self.user_id,
        )
        self.assertEqual(updated.default_sets, 4)
        self.assertEqual(updated.default_reps, 0)
        self.assertEqual(updated.default_time, 2)

    def test_update_strength_exercise_default_weight(self) -> None:
        exercise = services.create_exercise(
            {"name": "Bench Press"}, user_id=self.user_id
        )
        updated = services.update_exercise(
            exercise,
            {"default_weight": "20.00", "default_weight_unit": "kg"},
            user_id=self.user_id,
        )
        self.assertEqual(str(updated.default_weight), "20.00")
        self.assertEqual(updated.default_weight_unit, "kg")

    def test_timed_set_exercise_can_have_default_weight(self) -> None:
        exercise = services.create_exercise(
            {
                "name": "Weighted Plank",
                "prescription_type": "timed_sets",
                "default_weight": "10.00",
                "default_weight_unit": "kg",
            },
            user_id=self.user_id,
        )
        self.assertEqual(str(exercise.default_weight), "10.00")
        self.assertEqual(exercise.default_weight_unit, "kg")
