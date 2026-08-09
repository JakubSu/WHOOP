from __future__ import annotations

from typing import cast

from django.contrib.auth import get_user_model
from django.http import StreamingHttpResponse
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from coach.models import CoachConversation, CoachMessage
from recommendation.models import Recommendation, RecommendationOperation
from training.models import Exercise

SCENARIO_FACTORY = "ai.implementations.scenario.create_scenario_runner"


@override_settings(COACH_RUNNER_FACTORY=SCENARIO_FACTORY)
class ScenarioRunnerApiTests(TransactionTestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="scenario-api@example.com", password="strong-password"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.conversation = CoachConversation.objects.create(user=self.user)
        Exercise.objects.create(
            user_id="", name="Scenario press", muscle_group="chest", prescription_type="strength"
        )

    def test_message_code_persists_and_attaches_recommendation(self) -> None:
        response = self.client.post(
            f"/api/v1/coach/conversations/{self.conversation.id}/messages",
            {"content": "/test propose-new-workout"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        recommendation = Recommendation.objects.get()
        message = CoachMessage.objects.get(role=CoachMessage.Role.ASSISTANT)
        self.assertEqual(recommendation.coach_message_id, message.id)
        self.assertEqual(response.json()["recommendation"]["id"], str(recommendation.id))

    def test_stream_emits_tool_activities_and_recommendation_card(self) -> None:
        response = self.client.post(
            f"/api/v1/coach/conversations/{self.conversation.id}/messages/stream",
            {"content": "/test propose-new-workout"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = b"".join(cast(StreamingHttpResponse, response).streaming_content).decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: tool_started", body)
        self.assertIn("event: tool_completed", body)
        self.assertIn("event: completed", body)
        self.assertIn('"coach_card_snapshot"', body)

    def test_failed_scenario_expires_its_recommendation_without_saving_message(self) -> None:
        response = self.client.post(
            f"/api/v1/coach/conversations/{self.conversation.id}/messages",
            {"content": "/test fail-after-create"},
            format="json",
        )

        self.assertEqual(response.status_code, 503)
        recommendation = Recommendation.objects.get()
        operation = recommendation.operations.get()
        self.assertEqual(recommendation.status, Recommendation.Status.EXPIRED)
        self.assertEqual(operation.status, RecommendationOperation.Status.STALE)
        self.assertFalse(
            CoachMessage.objects.filter(conversation=self.conversation).exists()
        )
