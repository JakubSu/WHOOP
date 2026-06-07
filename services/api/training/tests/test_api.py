from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from training.models import Workout


class TrainingApiOwnershipTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = cast(Any, User.objects).create_user(
            email="one@example.com", password="strong-password"
        )
        self.other_user = cast(Any, User.objects).create_user(
            email="two@example.com", password="strong-password"
        )
        client = APIClient()
        client.force_authenticate(self.user)
        self.client = client

    def test_workout_create_uses_authenticated_user_id(self) -> None:
        response = self.client.post(
            reverse("workout-collection"),
            {"name": "Upper Body", "user_id": str(self.other_user.id)},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        workout = Workout.objects.get()
        self.assertEqual(workout.user_id, str(self.user.id))

    def test_workout_list_is_scoped_to_authenticated_user(self) -> None:
        Workout.objects.create(name="Mine", user_id=str(self.user.id))
        Workout.objects.create(name="Theirs", user_id=str(self.other_user.id))

        response = self.client.get(reverse("workout-collection"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Mine")

    def test_detail_does_not_return_other_user_workout(self) -> None:
        workout = Workout.objects.create(name="Theirs", user_id=str(self.other_user.id))

        response = self.client.get(reverse("workout-detail", args=[workout.id]))

        self.assertEqual(response.status_code, 404)

    def test_training_endpoints_require_authentication(self) -> None:
        client = APIClient()

        response = cast(Any, client.get(reverse("workout-collection")))

        self.assertEqual(response.status_code, 401)
