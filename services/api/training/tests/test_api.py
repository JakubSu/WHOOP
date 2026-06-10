from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from training.models import Exercise, Workout


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


class WorkoutSnapshotApiTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = cast(Any, User.objects).create_user(
            email="snapshot-one@example.com",
            password="strong-password",
        )
        self.other_user = cast(Any, User.objects).create_user(
            email="snapshot-two@example.com",
            password="strong-password",
        )
        client = APIClient()
        client.force_authenticate(self.user)
        self.client = client
        self.exercise = Exercise.objects.create(
            name="Bench Press",
            user_id=str(self.user.id),
            category=Exercise.Category.STRENGTH,
        )

    def test_snapshot_endpoints_require_authentication(self) -> None:
        client = APIClient()

        response = cast(Any, client.get(reverse("workout-snapshot-collection")))

        self.assertEqual(response.status_code, 401)

    def test_create_snapshot_uses_authenticated_user_and_returns_full_snapshot(self) -> None:
        response = self.client.post(
            reverse("workout-snapshot-collection"),
            {
                "name": "Upper Body",
                "user_id": str(self.other_user.id),
                "exercises": [
                    {
                        "snapshot_exercise_key": "bench-a",
                        "exercise": str(self.exercise.id),
                        "position": 1,
                        "sets": 4,
                        "reps": 8,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["user_id"], str(self.user.id))
        self.assertIn("version", body)
        self.assertEqual(body["exercises"][0]["workout_exercise_id"], body["exercises"][0]["snapshot_exercise_key"])
        self.assertEqual(body["exercises"][0]["exercise"]["name"], "Bench Press")

    def test_snapshot_list_is_scoped_to_authenticated_user(self) -> None:
        Workout.objects.create(name="Mine", user_id=str(self.user.id))
        Workout.objects.create(name="Theirs", user_id=str(self.other_user.id))

        response = self.client.get(reverse("workout-snapshot-collection"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Mine")

    def test_snapshot_detail_does_not_return_other_user_workout(self) -> None:
        workout = Workout.objects.create(name="Theirs", user_id=str(self.other_user.id))

        response = self.client.get(reverse("workout-snapshot-detail", args=[workout.id]))

        self.assertEqual(response.status_code, 404)

    def test_snapshot_patch_rejects_stale_version(self) -> None:
        create_response = self.client.post(
            reverse("workout-snapshot-collection"),
            {"name": "Upper Body"},
            format="json",
        )
        workout_id = create_response.json()["id"]

        response = self.client.patch(
            reverse("workout-snapshot-detail", args=[workout_id]),
            {"expected_version": "stale-version", "name": "Upper Strength"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_snapshot_patch_replaces_exercises_when_exercises_key_is_present(self) -> None:
        create_response = self.client.post(
            reverse("workout-snapshot-collection"),
            {
                "name": "Upper Body",
                "exercises": [
                    {
                        "snapshot_exercise_key": "bench-a",
                        "exercise": str(self.exercise.id),
                        "position": 1,
                    }
                ],
            },
            format="json",
        )
        body = create_response.json()

        response = self.client.patch(
            reverse("workout-snapshot-detail", args=[body["id"]]),
            {
                "expected_version": body["version"],
                "exercises": [
                    {
                        "workout_exercise_id": body["exercises"][0]["workout_exercise_id"],
                        "snapshot_exercise_key": body["exercises"][0]["snapshot_exercise_key"],
                        "exercise": str(self.exercise.id),
                        "position": 1,
                        "sets": 5,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["exercises"][0]["sets"], 5)

    def test_snapshot_create_rejects_invalid_nested_exercise(self) -> None:
        response = self.client.post(
            reverse("workout-snapshot-collection"),
            {
                "name": "Upper Body",
                "exercises": [
                    {
                        "exercise": str(self.exercise.id),
                        "position": 1,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
