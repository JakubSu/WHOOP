from typing import Any, cast
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from recommendation.models import Recommendation, RecommendationOperation
from training.models import Exercise, Workout, WorkoutExercise


class RecommendationApiTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = cast(Any, User.objects).create_user(
            email="recommendation-one@example.com",
            password="strong-password",
        )
        self.other_user = cast(Any, User.objects).create_user(
            email="recommendation-two@example.com",
            password="strong-password",
        )
        client = APIClient()
        client.force_authenticate(self.user)
        self.client = client
        self.exercise = Exercise.objects.create(name="Bench Press", user_id=str(self.user.id))
        self.replacement = Exercise.objects.create(name="Goblet Squat", user_id="")
        self.workout = Workout.objects.create(name="Upper Body", user_id=str(self.user.id))
        self.workout_exercise = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=5,
            reps=5,
        )
        self.workout_exercise_id = str(self.workout_exercise.id)

    def test_recommendation_endpoints_require_authentication(self) -> None:
        client = APIClient()

        response = cast(
            Any,
            client.get(reverse("recommendation-detail", args=["00000000-0000-0000-0000-000000000000"])),
        )

        self.assertEqual(response.status_code, 401)

    def test_detail_is_scoped_to_authenticated_user(self) -> None:
        recommendation = Recommendation.objects.create(
            user_id=str(self.other_user.id),
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Other",
        )

        response = self.client.get(reverse("recommendation-detail", args=[recommendation.id]))

        self.assertEqual(response.status_code, 404)

    def test_detail_returns_operations_with_display_text(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "replace_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.workout_exercise_id,
                        "replacement_exercise_id": str(self.replacement.id),
                    },
                }
            ]
        )

        response = self.client.get(reverse("recommendation-detail", args=[recommendation.id]))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["operations"][0]["display_text"], "Replace Bench Press with Goblet Squat")

    def test_generate_returns_created_recommendation(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "remove_exercise",
                    "payload_json": {"workout_exercise_id": self.workout_exercise_id},
                }
            ]
        )

        with patch(
            "recommendation.api.views.recommendation.services.generate_recommendation_for_workout",
            return_value=recommendation,
        ) as generate:
            response = self.client.post(
                reverse("recommendation-generate", args=[self.workout.id]),
                {},
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], str(recommendation.id))
        generate.assert_called_once_with(str(self.user.id), str(self.workout.id))

    def test_approve_operation_applies_only_that_operation(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.workout_exercise_id,
                        "changes": {"sets": 3},
                    },
                }
            ]
        )
        operation = recommendation.operations.get()

        response = self.client.post(
            reverse("recommendation-operation-approve", args=[recommendation.id, operation.id]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "accepted")
        self.assertEqual(response.json()["operations"][0]["status"], "accepted")
        self.assertEqual(WorkoutExercise.objects.get(pk=self.workout_exercise_id).sets, 3)

    def test_approve_operation_returns_conflict_for_stale_expected_version(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.workout_exercise_id,
                        "changes": {"sets": 3},
                    },
                }
            ]
        )
        operation = recommendation.operations.get()

        response = self.client.post(
            reverse("recommendation-operation-approve", args=[recommendation.id, operation.id]),
            {"expected_workout_version": "stale"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_reject_operation_marks_operation_rejected(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.workout_exercise_id,
                        "changes": {"sets": 3},
                    },
                }
            ]
        )
        operation = recommendation.operations.get()

        response = self.client.post(
            reverse("recommendation-operation-reject", args=[recommendation.id, operation.id]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "rejected")
        self.assertEqual(response.json()["operations"][0]["status"], "rejected")

    def test_legacy_recommendation_mutation_endpoints_return_bad_request(self) -> None:
        recommendation = self._create_recommendation([])

        approve_response = self.client.post(reverse("recommendation-approve", args=[recommendation.id]), {}, format="json")
        reject_response = self.client.post(reverse("recommendation-reject", args=[recommendation.id]), {}, format="json")

        self.assertEqual(approve_response.status_code, 400)
        self.assertEqual(reject_response.status_code, 400)

    def _create_recommendation(self, operations: list[dict[str, Any]]) -> Recommendation:
        recommendation = Recommendation.objects.create(
            user_id=str(self.user.id),
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Test recommendation",
        )
        for index, operation in enumerate(operations, start=1):
            RecommendationOperation.objects.create(
                recommendation=recommendation,
                sequence=index,
                operation_type=operation["operation_type"],
                payload_json=operation["payload_json"],
            )
        return recommendation
