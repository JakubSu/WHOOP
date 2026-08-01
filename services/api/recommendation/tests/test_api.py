from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from training.models import Exercise, Workout, WorkoutExercise

from recommendation.models import Recommendation


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
        self.workout = Workout.objects.create(
            name="Upper Body",
            date="2026-06-09",
            user_id=str(self.user.id),
        )
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

    def test_list_returns_authenticated_users_recommendations(self) -> None:
        mine = self._create_recommendation("remove_exercise", {"workout_exercise_id": self.workout_exercise_id})
        Recommendation.objects.create(
            user_id=str(self.other_user.id),
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Other",
            operation_type="remove_exercise",
            payload_json={"workout_exercise_id": self.workout_exercise_id},
        )

        response = self.client.get(reverse("recommendation-collection"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [str(mine.id)])

    def test_detail_is_scoped_to_authenticated_user(self) -> None:
        recommendation = Recommendation.objects.create(
            user_id=str(self.other_user.id),
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Other",
            operation_type="remove_exercise",
            payload_json={"workout_exercise_id": self.workout_exercise_id},
        )

        response = self.client.get(reverse("recommendation-detail", args=[recommendation.id]))

        self.assertEqual(response.status_code, 404)

    def test_detail_returns_operation_payload_with_display_text(self) -> None:
        recommendation = self._create_recommendation(
            "replace_exercise",
            {
                "workout_exercise_id": self.workout_exercise_id,
                "replacement_exercise_id": str(self.replacement.id),
            },
        )

        response = self.client.get(reverse("recommendation-detail", args=[recommendation.id]))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["operation_type"], "replace_exercise")
        self.assertEqual(body["payload"]["replacement_exercise_id"], str(self.replacement.id))
        self.assertEqual(body["display_text"], "Replace Bench Press with Goblet Squat")

    def test_accept_recommendation_applies_operation(self) -> None:
        recommendation = self._create_recommendation(
            "update_exercise",
            {
                "workout_exercise_id": self.workout_exercise_id,
                "changes": {"sets": 3},
            },
        )

        response = self.client.post(
            reverse("recommendation-accept", args=[recommendation.id]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "applied")
        self.assertEqual(WorkoutExercise.objects.get(pk=self.workout_exercise_id).sets, 3)

    def test_accept_returns_conflict_for_stale_expected_version(self) -> None:
        recommendation = self._create_recommendation(
            "update_exercise",
            {
                "workout_exercise_id": self.workout_exercise_id,
                "changes": {"sets": 3},
            },
        )

        response = self.client.post(
            reverse("recommendation-accept", args=[recommendation.id]),
            {"expected_workout_version": "stale"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_reject_recommendation_marks_rejected(self) -> None:
        recommendation = self._create_recommendation(
            "update_exercise",
            {
                "workout_exercise_id": self.workout_exercise_id,
                "changes": {"sets": 3},
            },
        )

        response = self.client.post(
            reverse("recommendation-reject", args=[recommendation.id]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "rejected")
        self.assertEqual(WorkoutExercise.objects.get(pk=self.workout_exercise_id).sets, 5)

    def test_patch_status_can_reject_pending_recommendation(self) -> None:
        recommendation = self._create_recommendation(
            "remove_exercise",
            {"workout_exercise_id": self.workout_exercise_id},
        )

        response = self.client.patch(
            reverse("recommendation-detail", args=[recommendation.id]),
            {"status": "rejected"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "rejected")

    def _create_recommendation(self, operation_type: str, payload: dict[str, Any]) -> Recommendation:
        return Recommendation.objects.create(
            user_id=str(self.user.id),
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Test recommendation",
            operation_type=operation_type,
            payload_json=payload,
        )
