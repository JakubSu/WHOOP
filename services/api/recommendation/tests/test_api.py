from datetime import date
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from coach.models import CoachConversation
from recommendation.contracts import RecommendationDraft
from recommendation.services import create_recommendation
from training.models import Exercise, Workout, WorkoutExercise


class RecommendationDetailApiTests(TestCase):
    """Verifies the card metadata consumed with Workout API data."""

    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = cast(Any, user_model.objects).create_user(
            email="recommendation-api@example.com", password="strong-password"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.conversation = CoachConversation.objects.create(user=self.user)
        self.workout = Workout.objects.create(
            user_id=str(self.user.id), name="Strength", date=date(2026, 8, 13)
        )
        self.exercise = Exercise.objects.create(
            name="Squat",
            muscle_group=Exercise.MuscleGroup.QUADS,
            prescription_type=Exercise.PrescriptionType.STRENGTH,
        )

    def test_detail_groups_existing_workouts_by_id_without_embedding_them(self) -> None:
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Rename workout",
                    "operations": [{
                        "operation_type": "update_workout",
                        "reason": "Match the new focus.",
                        "payload": {"workout_id": str(self.workout.id), "changes": {"name": "Lower body"}},
                    }],
                }
            ),
        )

        response = self.client.get(f"/api/v1/recommendations/{recommendation.id}/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("workouts", body)
        self.assertEqual(body["groups"], [{
            "id": str(self.workout.id),
            "title": "Strength",
            "target": {"kind": "existing", "workout_id": str(self.workout.id)},
            "operation_ids": [str(recommendation.operations.get().id)],
        }])

    def test_detail_includes_new_workout_draft_for_the_unpersisted_preview(self) -> None:
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Add conditioning",
                    "operations": [
                        {
                            "operation_type": "add_workout",
                            "reason": "Build capacity.",
                            "payload": {
                                "temporary_id": "conditioning",
                                "name": "Conditioning",
                                "date": "2026-08-14",
                                "expected_time": 30,
                            },
                        },
                        {
                            "operation_type": "add_exercise",
                            "reason": "Add a simple interval.",
                            "payload": {
                                "workout": {"kind": "new", "temporary_id": "conditioning"},
                                "exercise_id": str(self.exercise.id),
                                "prescription": {"type": "reps", "sets": 3, "reps": 10},
                                "position": 0,
                            },
                        },
                    ],
                }
            ),
        )

        response = self.client.get(f"/api/v1/recommendations/{recommendation.id}/")

        self.assertEqual(response.status_code, 200)
        group = response.json()["groups"][0]
        self.assertEqual(group["target"]["kind"], "new")
        self.assertEqual(group["target"]["draft"]["name"], "Conditioning")
        self.assertEqual(len(group["operation_ids"]), 2)

    def test_accepting_new_workout_returns_its_persisted_workout_id(self) -> None:
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Add conditioning",
                    "operations": [{
                        "operation_type": "add_workout",
                        "reason": "Build capacity.",
                        "payload": {
                            "temporary_id": "conditioning",
                            "name": "Conditioning",
                            "date": "2026-08-14",
                        },
                    }],
                }
            ),
        )

        response = self.client.post(f"/api/v1/recommendations/{recommendation.id}/accept/")

        self.assertEqual(response.status_code, 200)
        target = response.json()["groups"][0]["target"]
        self.assertEqual(target["kind"], "existing")
        self.assertTrue(Workout.objects.filter(pk=target["workout_id"]).exists())

    def test_detail_groups_a_pending_exercise_move_under_source_and_target_workouts(self) -> None:
        target = Workout.objects.create(
            user_id=str(self.user.id), name="Conditioning", date=date(2026, 8, 14)
        )
        workout_exercise = WorkoutExercise.objects.create(
            workout=self.workout, exercise=self.exercise, sets=3, reps=10
        )
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Move squat",
                    "operations": [{
                        "operation_type": "update_exercise",
                        "reason": "Pair it with conditioning.",
                        "payload": {
                            "workout_exercise_id": str(workout_exercise.id),
                            "target_workout_id": str(target.id),
                        },
                    }],
                }
            ),
        )

        response = self.client.get(f"/api/v1/recommendations/{recommendation.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {group["target"]["workout_id"] for group in response.json()["groups"]},
            {str(self.workout.id), str(target.id)},
        )
