from django.test import TestCase

from training import services
from training.models import Workout


class WorkoutServiceTests(TestCase):
    user_id = "user-1"

    def test_create_workout(self) -> None:
        starting_count = Workout.objects.count()
        training_plan = services.create_training_plan({"name": "Strength Block"}, user_id=self.user_id)
        workout = services.create_workout(
            {
                "plan": str(training_plan.id),
                "name": "Upper Body",
                "date": "2026-06-09",
                "expected_time": 45,
            },
            user_id=self.user_id,
        )
        self.assertEqual(workout.name, "Upper Body")
        self.assertEqual(workout.plan, training_plan)
        self.assertEqual(workout.user_id, self.user_id)
        self.assertEqual(str(workout.date), "2026-06-09")
        self.assertEqual(workout.expected_time, 45)
        self.assertEqual(Workout.objects.count(), starting_count + 1)

    def test_update_workout_expected_time(self) -> None:
        workout = services.create_workout({"name": "Upper Body"}, user_id=self.user_id)
        updated = services.update_workout(workout, {"expected_time": 60}, user_id=self.user_id)
        self.assertEqual(updated.expected_time, 60)
