from django.test import TestCase

from training import services
from training.models import TrainingPlan


class TrainingPlanServiceTests(TestCase):
    user_id = "user-1"

    def test_create_training_plan(self) -> None:
        starting_count = TrainingPlan.objects.count()
        training_plan = services.create_training_plan(
            {
                "name": "Summer Strength Block",
                "start_date": "2026-06-01",
                "end_date": "2026-07-01",
            },
            user_id=self.user_id,
        )
        self.assertEqual(training_plan.name, "Summer Strength Block")
        self.assertEqual(training_plan.user_id, self.user_id)
        self.assertEqual(str(training_plan.start_date), "2026-06-01")
        self.assertEqual(str(training_plan.end_date), "2026-07-01")
        self.assertEqual(TrainingPlan.objects.count(), starting_count + 1)
