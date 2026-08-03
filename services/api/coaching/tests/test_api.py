from collections.abc import Iterable
from typing import Any, cast
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse, StreamingHttpResponse
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from ai.coach.schemas import CoachTurnDraft
from coaching.models import CoachConversation
from recommendation.models import Recommendation
from training.models import Exercise, Workout, WorkoutExercise


class FakeCoachGenerator:
    def __init__(self, draft: CoachTurnDraft) -> None:
        self.draft = draft

    def generate(self, context: dict[str, Any]) -> CoachTurnDraft:
        return self.draft


class CoachApiTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = cast(Any, User.objects).create_user(
            email="coach-one@example.com",
            password="strong-password",
        )
        self.other_user = cast(Any, User.objects).create_user(
            email="coach-two@example.com",
            password="strong-password",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.exercise = Exercise.objects.create(
            name="Bench Press", user_id=str(self.user.id)
        )
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

    def test_coach_endpoints_require_authentication(self) -> None:
        client = APIClient()

        stream_response = client.post(
            reverse("coach-turn-stream"),
            {
                "page_context": {
                    "page_type": "workout",
                    "context_id": str(self.workout.id),
                },
                "message": "Help me adjust this workout.",
            },
            format="json",
        )
        messages_response = client.get(
            reverse(
                "coach-conversation-messages",
                args=["00000000-0000-0000-0000-000000000000"],
            )
        )

        stream_response = cast(HttpResponse, stream_response)
        messages_response = cast(HttpResponse, messages_response)
        self.assertEqual(stream_response.status_code, 401)
        self.assertEqual(messages_response.status_code, 401)

    def test_user_cannot_read_another_users_conversation(self) -> None:
        conversation = CoachConversation.objects.create(
            user_id=str(self.other_user.id),
            page_type=CoachConversation.PageType.WORKOUT,
            context_id=str(self.workout.id),
        )

        response = self.client.get(
            reverse("coach-conversation-messages", args=[conversation.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_active_conversation_lookup_returns_messages_without_creating_conversation(
        self,
    ) -> None:
        empty_response = self.client.get(
            reverse("coach-active-conversation"),
            {
                "page_type": "workout",
                "context_id": str(self.workout.id),
            },
        )

        self.assertEqual(empty_response.status_code, 204)
        self.assertEqual(CoachConversation.objects.count(), 0)

        conversation = CoachConversation.objects.create(
            user_id=str(self.user.id),
            page_type=CoachConversation.PageType.WORKOUT,
            context_id=str(self.workout.id),
        )
        conversation.messages.create(role="user", content="What should I focus on?")
        conversation.messages.create(role="assistant", content="Keep the bench crisp.")

        response = self.client.get(
            reverse("coach-active-conversation"),
            {
                "page_type": "workout",
                "context_id": str(self.workout.id),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["conversation_id"], str(conversation.id))
        self.assertEqual(
            [message["content"] for message in response.json()["messages"]],
            ["What should I focus on?", "Keep the bench crisp."],
        )

    @patch("whoop.services.create_summary_service")
    def test_streamed_turn_creates_conversation_messages_and_ordered_sse_events(
        self,
        summary_factory: Any,
    ) -> None:
        summary_factory.return_value.execute.return_value = {
            "connected": True,
            "recovery_score": 42,
        }
        draft = CoachTurnDraft.model_validate(
            {
                "answer": "I would reduce the bench volume today.",
                "progress_summaries": ["Checking recovery and workout context."],
                "workout_patch": {
                    "summary": "Reduce pressing volume.",
                    "reason": "Recovery is lower today.",
                    "operation": {
                        "op": "update_exercise",
                        "workout_exercise_id": str(self.workout_exercise.id),
                        "changes": {"sets": 3},
                        "reason": "Keep the movement but lower volume.",
                    },
                },
            }
        )

        with patch(
            "coaching.api.views.CoachOrchestrator",
            return_value=__import__(
                "ai.coach.orchestrator", fromlist=["CoachOrchestrator"]
            ).CoachOrchestrator(generator=FakeCoachGenerator(draft)),
        ):
            response = self.client.post(
                reverse("coach-turn-stream"),
                {
                    "page_context": {
                        "page_type": "workout",
                        "context_id": str(self.workout.id),
                    },
                    "message": "Make this easier because my knee hurts.",
                },
                format="json",
                HTTP_ACCEPT="text/event-stream",
            )

        self.assertEqual(response.status_code, 200)
        response = cast(StreamingHttpResponse, response)
        body = b"".join(cast(Iterable[bytes], response.streaming_content)).decode(
            "utf-8"
        )
        self.assertIn("event: conversation_started", body)
        self.assertIn("event: assistant_progress", body)
        self.assertIn("event: recommendation_created", body)
        self.assertIn("event: assistant_done", body)
        self.assertLess(
            body.index("event: conversation_started"),
            body.index("event: assistant_done"),
        )

        conversation = CoachConversation.objects.get(user_id=str(self.user.id))
        self.assertEqual(conversation.messages.count(), 2)
        assistant_message = conversation.messages.get(role="assistant")
        self.assertEqual(
            assistant_message.content, "I would reduce the bench volume today."
        )
        self.assertIn(
            "pain_or_injury_mentioned", assistant_message.metadata_json["safety_flags"]
        )
        self.assertTrue(
            Recommendation.objects.filter(
                source=Recommendation.Source.COACH_CHAT
            ).exists()
        )

        history = self.client.get(
            reverse("coach-conversation-messages", args=[conversation.id])
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual(
            [message["role"] for message in history.json()["messages"]],
            ["user", "assistant"],
        )

    def test_streamed_turn_reuses_active_conversation_for_same_page_context(
        self,
    ) -> None:
        conversation = CoachConversation.objects.create(
            user_id=str(self.user.id),
            page_type=CoachConversation.PageType.WORKOUT,
            context_id=str(self.workout.id),
        )
        draft = CoachTurnDraft(answer="Keep it simple today.")

        with patch(
            "coaching.api.views.CoachOrchestrator",
            return_value=__import__(
                "ai.coach.orchestrator", fromlist=["CoachOrchestrator"]
            ).CoachOrchestrator(generator=FakeCoachGenerator(draft)),
        ):
            response = self.client.post(
                reverse("coach-turn-stream"),
                {
                    "page_context": {
                        "page_type": "workout",
                        "context_id": str(self.workout.id),
                    },
                    "message": "What should I focus on?",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        response = cast(StreamingHttpResponse, response)
        b"".join(cast(Iterable[bytes], response.streaming_content))
        self.assertEqual(CoachConversation.objects.count(), 1)
        conversation.refresh_from_db()
        self.assertEqual(conversation.messages.count(), 2)
