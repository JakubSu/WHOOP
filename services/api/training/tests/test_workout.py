from django.test import TestCase

from training import services
from training.models import Workout


class WorkoutServiceTests(TestCase):
    def test_create_workout(self) -> None:
        workout = services.create_workout({"name": "Upper Body", "workout_type": Workout.Type.STRENGTH})
        self.assertEqual(workout.name, "Upper Body")
        self.assertEqual(workout.status, Workout.Status.PLANNED)
        self.assertEqual(Workout.objects.count(), 1)

    def test_completed_workout_gets_completed_at(self) -> None:
        workout = services.create_workout({"name": "Upper Body"})
        updated = services.update_workout(workout, {"status": Workout.Status.COMPLETED})
        self.assertEqual(updated.status, Workout.Status.COMPLETED)
        self.assertIsNotNone(updated.completed_at)
