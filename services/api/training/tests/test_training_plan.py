from django.test import TestCase

from training import services
from training.models import TrainingPlan


class TrainingPlanServiceTests(TestCase):
    def test_create_training_plan(self) -> None:
        training_plan = services.create_training_plan(
            {
                "name": "Summer Strength Block",
                "goal": "Strength",
                "status": TrainingPlan.Status.ACTIVE,
            }
        )
        self.assertEqual(training_plan.name, "Summer Strength Block")
        self.assertEqual(training_plan.status, TrainingPlan.Status.ACTIVE)
        self.assertEqual(TrainingPlan.objects.count(), 1)
