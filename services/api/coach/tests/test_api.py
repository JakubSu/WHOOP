import asyncio
import json
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any, cast
from unittest.mock import AsyncMock, patch

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.http import StreamingHttpResponse
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from ai.runner import (
    ActivityChanged,
    CoachActivity,
    CoachRunFailed,
    CoachRunResult,
    RunCompleted,
    RunFailed,
    TextDelta,
)
from ai.tests.fakes import runner
from coach.api.views.messages import _with_sse_heartbeats
from coach.contracts.ui_actions import ExerciseResolutionUiActionDraft
from coach.models import (
    CoachBudgetReservation,
    CoachConversation,
    CoachMessage,
    UiAction,
)
from recommendation.contracts import RecommendationDraft
from recommendation.models import Recommendation, RecommendationOperation
from recommendation.services import create_recommendation
from training.models import Exercise, Workout


async def _collect_stream(response: StreamingHttpResponse) -> bytes:
    return b"".join([item async for item in response.streaming_content])  # type: ignore[misc]


async def _closing_heartbeat_stream_closes_source() -> bool:
    closed = False

    async def source():
        nonlocal closed
        try:
            await asyncio.sleep(60)
            yield b"unreachable"
        finally:
            closed = True

    stream = _with_sse_heartbeats(source(), interval_seconds=0.001)
    await anext(stream)
    await cast(Any, stream).aclose()
    return closed


class CoachConversationApiTests(TestCase):
    """Verifies the Coach conversation, message, and streaming API contracts."""

    def setUp(self) -> None:
        """Creates two authenticated users and a client for the conversation owner."""

        user_model = get_user_model()
        self.user = cast(Any, user_model.objects).create_user(
            email="coach-owner@example.com",
            password="strong-password",
        )
        self.other_user = cast(Any, user_model.objects).create_user(
            email="other-owner@example.com",
            password="strong-password",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def tearDown(self) -> None:
        """Restores the shared scripted runner after each test."""

        runner.requests.clear()
        runner.events = []
        runner.result = CoachRunResult(content="Ready.", ai_message_batch=[])
        runner.stream_delay = 0

    def test_closing_idle_heartbeat_stream_closes_the_sse_iterator(self) -> None:
        self.assertTrue(async_to_sync(_closing_heartbeat_stream_closes_source)())

    def test_user_can_create_and_list_only_their_conversations(self) -> None:
        """Users see only their own newly created conversations in the sidebar list."""

        create_response = self.client.post(
            "/api/v1/coach/conversations", {}, format="json"
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertIsNone(create_response.json()["title"])

        other_client = APIClient()
        other_client.force_authenticate(self.other_user)
        other_client.post("/api/v1/coach/conversations", {}, format="json")

        list_response = self.client.get("/api/v1/coach/conversations")

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["results"]), 1)
        self.assertEqual(
            list_response.json()["results"][0]["id"],
            create_response.json()["id"],
        )
        self.assertIsNone(list_response.json()["results"][0]["last_message_preview"])

    @override_settings(
        COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner",
        COACH_MAX_COST_USD=Decimal("0.05"),
        COACH_USER_MONTHLY_BUDGET_USD=Decimal("0.05"),
        COACH_GLOBAL_MONTHLY_BUDGET_USD=Decimal("1.00"),
    )
    def test_monthly_budget_blocks_a_second_coach_message(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)
        runner.result = CoachRunResult(
            content="Ready.", ai_message_batch=[], cost_usd=Decimal("0.05")
        )

        first = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages",
            {"content": "First request"},
            format="json",
        )
        second = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages",
            {"content": "Second request"},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["code"], "monthly_budget_exceeded")

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_non_stream_failure_settles_the_known_provider_cost(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)
        failure = CoachRunFailed(
            RunFailed(code="timeout", retryable=True, cost_usd=Decimal("0.02"))
        )

        with patch.object(runner, "run", new=AsyncMock(side_effect=failure)):
            response = self.client.post(
                f"/api/v1/coach/conversations/{conversation.id}/messages",
                {"content": "Try this"},
                format="json",
            )

        reservation = CoachBudgetReservation.objects.get()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(reservation.status, CoachBudgetReservation.Status.SETTLED)
        self.assertEqual(reservation.actual_usd, Decimal("0.02"))

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_closing_an_unstarted_stream_releases_its_budget_reservation(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages/stream",
            {"content": "Start but do not stream"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        cast(StreamingHttpResponse, response).close()

        reservation = CoachBudgetReservation.objects.get()
        self.assertEqual(reservation.status, CoachBudgetReservation.Status.RELEASED)

    def test_conversation_crud_hides_other_users_resources(self) -> None:
        """Conversation reads, updates, and deletion enforce ownership."""

        conversation = CoachConversation.objects.create(user=self.user)
        other = CoachConversation.objects.create(user=self.other_user)

        patch = self.client.patch(
            f"/api/v1/coach/conversations/{conversation.id}",
            {"title": " Marathon adjustments "},
            format="json",
        )
        hidden = self.client.get(f"/api/v1/coach/conversations/{other.id}")
        deleted = self.client.delete(f"/api/v1/coach/conversations/{conversation.id}")

        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["title"], "Marathon adjustments")
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(CoachConversation.objects.filter(pk=conversation.id).exists())

    def test_conversation_list_uses_a_stable_cursor(self) -> None:
        """Conversation history uses a cursor to return subsequent sidebar pages."""

        for index in range(21):
            CoachConversation.objects.create(user=self.user, title=f"Chat {index}")

        first = self.client.get("/api/v1/coach/conversations")
        second = self.client.get(
            "/api/v1/coach/conversations", {"cursor": first.json()["next"]}
        )

        self.assertEqual(len(first.json()["results"]), 20)
        self.assertIsNotNone(first.json()["next"])
        self.assertEqual(len(second.json()["results"]), 1)
        self.assertIsNone(second.json()["next"])

    def test_message_history_is_backward_paginated_and_hides_ai_history(self) -> None:
        """Message history pages backward without exposing private model history."""

        conversation = CoachConversation.objects.create(user=self.user)
        for index in range(31):
            message = CoachMessage.objects.create(
                conversation=conversation,
                role="assistant" if index % 2 else "user",
                content=f"Message {index:02d}",
                ai_message_batch=[{"secret": index}] if index % 2 else None,
                activity_log=(
                    [
                        {
                            "id": str(uuid.uuid4()),
                            "kind": "other",
                            "label": "Working on your request…",
                            "status": "completed",
                        }
                    ]
                    if index % 2
                    else []
                ),
            )
            CoachMessage.objects.filter(pk=message.pk).update(
                created_at=timezone.now() + timedelta(seconds=index)
            )

        newest = self.client.get(
            f"/api/v1/coach/conversations/{conversation.id}/messages"
        )
        older = self.client.get(
            f"/api/v1/coach/conversations/{conversation.id}/messages",
            {"cursor": newest.json()["next"]},
        )

        self.assertEqual(len(newest.json()["results"]), 30)
        self.assertEqual(newest.json()["results"][0]["content"], "Message 01")
        self.assertEqual(newest.json()["results"][-1]["content"], "Message 30")
        self.assertNotIn("ai_message_batch", newest.json()["results"][0])
        self.assertEqual(older.json()["results"][0]["content"], "Message 00")
        self.assertEqual(older.json()["results"][0]["activities"], [])

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_message_run_receives_ordered_ai_batches_and_persists_complete_turn(
        self,
    ) -> None:
        """A completed turn receives ordered AI history and saves its visible result."""

        conversation = CoachConversation.objects.create(user=self.user)
        CoachMessage.objects.create(
            conversation=conversation,
            role=CoachMessage.Role.USER,
            content="Earlier request",
        )
        CoachMessage.objects.create(
            conversation=conversation,
            role=CoachMessage.Role.ASSISTANT,
            content="Earlier",
            ai_message_batch=[{"batch": 1}],
        )
        activity_id = str(uuid.uuid4())
        runner.result = CoachRunResult(
            content="Reduce today’s volume.",
            ai_message_batch=[{"batch": 2}],
            activities=[
                CoachActivity(
                    id=activity_id,
                    kind="recovery_data",
                    label="unsafe runner label",
                    status="completed",
                )
            ],
        )

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages",
            {"content": "Should I train today?"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(runner.requests[0].history.turns[-1].raw_batch, [{"batch": 1}])
        self.assertEqual(response.json()["content"], "Reduce today’s volume.")
        self.assertEqual(
            response.json()["activities"][0]["label"],
            "Fetching your recovery data…",
        )
        self.assertEqual(conversation.messages.count(), 4)
        saved = conversation.messages.get(content="Reduce today’s volume.")
        self.assertEqual(saved.ai_message_batch, [{"batch": 2}])

    @override_settings(
        COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner",
        COACH_CONTEXT_RECENT_TURNS=3,
    )
    def test_message_run_uses_three_raw_turns_and_older_visible_turns(self) -> None:
        """Older displayed exchanges are separate from the newest private batches."""

        conversation = CoachConversation.objects.create(user=self.user)
        for index in range(6):
            user_message = CoachMessage.objects.create(
                conversation=conversation,
                role=CoachMessage.Role.USER,
                content=f"User {index}",
            )
            assistant_message = CoachMessage.objects.create(
                conversation=conversation,
                role=CoachMessage.Role.ASSISTANT,
                content=f"Coach {index}",
                ai_message_batch=[{"batch": index}],
            )
            message_time = timezone.now() + timedelta(seconds=index * 2)
            CoachMessage.objects.filter(pk=user_message.pk).update(
                created_at=message_time
            )
            CoachMessage.objects.filter(pk=assistant_message.pk).update(
                created_at=message_time + timedelta(seconds=1)
            )

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages",
            {"content": "New request"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        request = runner.requests[0]
        self.assertEqual(
            [turn.raw_batch for turn in request.history.turns if turn.raw_batch],
            [[{"batch": 3}], [{"batch": 4}], [{"batch": 5}]],
        )
        self.assertEqual(
            [
                (turn.user_content, turn.assistant_content)
                for turn in request.history.turns[:2]
            ],
            [("User 0", "Coach 0"), ("User 1", "Coach 1")],
        )
        self.assertEqual(
            [
                (turn.user_content, turn.assistant_content)
                for turn in request.history.turns[2:]
            ],
            [
                ("User 2", "Coach 2"),
                ("User 3", "Coach 3"),
                ("User 4", "Coach 4"),
                ("User 5", "Coach 5"),
            ],
        )

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_stream_uses_owned_events_and_never_leaks_runner_labels(self) -> None:
        """The stream sanitizes runner details and links committed recommendation operations."""

        conversation = CoachConversation.objects.create(user=self.user)
        activity_id = str(uuid.uuid4())
        workout = Workout.objects.create(
            user_id=str(self.user.id), name="Tempo run", date="2026-08-05"
        )
        recommendation = create_recommendation(
            user=self.user,
            conversation=conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Reduce volume",
                    "operations": [
                        {
                            "operation_type": "update_workout",
                            "reason": "Keep the session manageable.",
                            "payload": {
                                "workout_id": str(workout.id),
                                "changes": {"name": "Easy session"},
                            },
                        }
                    ],
                }
            ),
        )
        runner.events = [
            ActivityChanged(
                CoachActivity(
                    id=activity_id,
                    kind="unknown",  # type: ignore[arg-type]
                    label="fetch_recovery(token=secret)",
                    status="running",
                )
            ),
            ActivityChanged(
                CoachActivity(
                    id=activity_id,
                    kind="unknown",  # type: ignore[arg-type]
                    label="raw tool output",
                    status="completed",
                )
            ),
            TextDelta("Your recovery is stable."),
            RunCompleted(
                CoachRunResult(
                    content="Your recovery is stable.",
                    ai_message_batch=[{"safe": "stored only"}],
                    recommendation_id=recommendation.id,
                )
            ),
        ]

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages/stream",
            {"content": "How am I doing?"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        response = cast(StreamingHttpResponse, response)
        body = async_to_sync(_collect_stream)(response).decode()
        events = _parse_events(body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(events[0]["event"], "message_started")
        self.assertEqual(events[1]["event"], "thinking_started")
        self.assertEqual(events[-1]["event"], "completed")
        self.assertEqual(
            events[-1]["data"]["message"]["recommendation"]["coach_card_snapshot"][
                "workout_groups"
            ][0]["summary"]["updated"],
            1,
        )
        self.assertTrue(events[-1]["data"]["message"]["recommendation"]["actionable"])
        self.assertEqual(events[-2]["event"], "thinking_finished")
        self.assertEqual(
            [item["data"]["sequence"] for item in events],
            list(range(len(events))),
        )
        self.assertNotIn("secret", body)
        self.assertNotIn("fetch_recovery", body)
        tool_event = next(item for item in events if item["event"] == "tool_started")
        self.assertEqual(tool_event["data"]["activity"]["kind"], "other")
        self.assertEqual(
            tool_event["data"]["activity"]["label"], "Working on your request…"
        )
        saved = conversation.messages.get(role=CoachMessage.Role.ASSISTANT)
        self.assertEqual(saved.activity_log[0]["status"], "completed")
        recommendation.refresh_from_db()
        self.assertEqual(recommendation.coach_message, saved)
        operation = RecommendationOperation.objects.get(recommendation=recommendation)
        self.assertEqual(operation.status, RecommendationOperation.Status.PENDING)

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_stream_exposes_a_runner_terminal_failure(self) -> None:
        """A terminal runner failure becomes a structured, retryable SSE error."""

        conversation = CoachConversation.objects.create(user=self.user)
        runner.events = [RunFailed(code="timeout", retryable=True)]

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages/stream",
            {"content": "How am I doing?"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = async_to_sync(_collect_stream)(cast(StreamingHttpResponse, response)).decode()
        events = _parse_events(body)

        self.assertEqual(events[-1]["event"], "error")
        self.assertEqual(events[-1]["data"]["code"], "timeout")
        self.assertTrue(events[-1]["data"]["retryable"])
        self.assertFalse(conversation.messages.exists())

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_stream_explains_a_context_limit_failure(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)
        runner.events = [RunFailed(code="context_limit", retryable=False)]

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages/stream",
            {"content": "Summarize my full training history."},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = async_to_sync(_collect_stream)(
            cast(StreamingHttpResponse, response)
        ).decode()
        error = _parse_events(body)[-1]["data"]

        self.assertEqual(error["code"], "context_limit")
        self.assertEqual(
            error["message"],
            "This message is too long for the coach to process. Start a new chat "
            "or send a shorter message.",
        )
        self.assertFalse(error["retryable"])

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_completed_turn_persists_and_serializes_ui_actions(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)
        runner.events = [
            RunCompleted(
                CoachRunResult(
                    content="Choose an exercise.",
                    ai_message_batch=[],
                    ui_actions=[
                        ExerciseResolutionUiActionDraft.model_validate(
                            {
                                "type": "exercise_resolution",
                                "payload": {
                                    "requested_name": "Landmine press",
                                    "draft_exercise": {
                                        "name": "Landmine press",
                                        "prescription_type": "strength",
                                        "muscle_group": "shoulders",
                                    },
                                },
                            }
                        )
                    ],
                )
            )
        ]
        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages/stream",
            {"content": "Add a landmine press."},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        events = _parse_events(
            async_to_sync(_collect_stream)(cast(StreamingHttpResponse, response)).decode()
        )
        action = events[-1]["data"]["message"]["ui_actions"][0]
        self.assertEqual(action["type"], "exercise_resolution")
        self.assertEqual(action["status"], "pending")
        self.assertEqual(action["payload"]["original_request"], "Add a landmine press.")
        self.assertTrue(UiAction.objects.filter(id=action["id"]).exists())

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_resolving_ui_action_starts_a_trusted_continuation(self) -> None:
        from training.models import Exercise

        conversation = CoachConversation.objects.create(user=self.user)
        message = CoachMessage.objects.create(
            conversation=conversation, role="assistant", content="Choose one."
        )
        action = UiAction.objects.create(
            message=message,
            type="exercise_resolution",
            payload={
                "requested_name": "Landmine press",
                "draft_exercise": {},
                "original_request": "Add a landmine press to my upper-body workout.",
            },
        )
        exercise = Exercise.objects.create(user_id=str(self.user.id), name="Landmine press")
        runner.events = [
            RunCompleted(
                CoachRunResult(
                    content="Choose another exercise.",
                    ai_message_batch=[],
                    ui_actions=[
                        ExerciseResolutionUiActionDraft.model_validate(
                            {
                                "type": "exercise_resolution",
                                "payload": {
                                    "requested_name": "Hip airplane",
                                    "draft_exercise": {
                                        "name": "Hip airplane",
                                        "prescription_type": "timed",
                                        "muscle_group": "glutes",
                                    },
                                },
                            }
                        )
                    ],
                )
            )
        ]
        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/ui-actions/{action.id}/resolve/stream",
            {"exercise_id": str(exercise.id)},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        body = async_to_sync(_collect_stream)(cast(StreamingHttpResponse, response)).decode()
        self.assertIn("event: completed", body)
        completed = _parse_events(body)[-1]["data"]
        original_message = next(
            item
            for item in completed["updated_messages"]
            if item["id"] == str(message.id)
        )
        self.assertEqual(original_message["ui_actions"][0]["status"], "resolved")
        action.refresh_from_db()
        self.assertEqual(action.status, UiAction.Status.RESOLVED)
        self.assertEqual(action.resolution["exercise_id"], str(exercise.id))
        self.assertIn(str(exercise.id), runner.requests[-1].content)
        self.assertIn(
            "Add a landmine press to my upper-body workout.",
            runner.requests[-1].content,
        )
        self.assertIn(
            "There may be no existing recommendation", runner.requests[-1].content
        )
        next_action = UiAction.objects.exclude(id=action.id).get()
        self.assertEqual(
            next_action.payload["original_request"],
            "Add a landmine press to my upper-body workout.",
        )
        self.assertEqual(
            CoachMessage.objects.filter(
                conversation=conversation, role=CoachMessage.Role.USER
            )
            .latest("created_at")
            .content,
            "Selected Landmine press.",
        )

    @override_settings(COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner")
    def test_created_exercise_resolution_is_visible_as_created(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)
        message = CoachMessage.objects.create(
            conversation=conversation, role="assistant", content="Choose one."
        )
        action = UiAction.objects.create(
            message=message,
            type="exercise_resolution",
            payload={"requested_name": "Landmine press", "draft_exercise": {}},
        )
        exercise = Exercise.objects.create(user_id=str(self.user.id), name="Landmine press")
        runner.events = [RunCompleted(CoachRunResult(content="Added.", ai_message_batch=[]))]

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/ui-actions/{action.id}/resolve/stream",
            {"exercise_id": str(exercise.id), "method": "created"},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )

        self.assertEqual(response.status_code, 200)
        async_to_sync(_collect_stream)(cast(StreamingHttpResponse, response))
        self.assertEqual(
            CoachMessage.objects.filter(
                conversation=conversation, role=CoachMessage.Role.USER
            )
            .latest("created_at")
            .content,
            "Created Landmine press.",
        )

    def test_user_can_dismiss_only_their_pending_ui_action(self) -> None:
        conversation = CoachConversation.objects.create(user=self.user)
        message = CoachMessage.objects.create(conversation=conversation, role="assistant", content="Choose.")
        action = UiAction.objects.create(message=message, type="exercise_resolution", payload={})
        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/ui-actions/{action.id}/dismiss"
        )
        self.assertEqual(response.status_code, 200)
        action.refresh_from_db()
        self.assertEqual(action.status, UiAction.Status.DISMISSED)
        self.assertEqual(response.json()["ui_actions"][0]["status"], "dismissed")

    @override_settings(
        COACH_RUNNER_FACTORY="ai.tests.fakes.create_runner",
        COACH_STREAM_KEEPALIVE_SECONDS=0.01,
    )
    def test_stream_sends_keepalive_comments_while_runner_is_quiet(self) -> None:
        """An idle response produces SSE heartbeat comments until it completes."""

        conversation = CoachConversation.objects.create(user=self.user)
        runner.stream_delay = 0.03
        runner.events = [
            RunCompleted(CoachRunResult(content="Done.", ai_message_batch=[]))
        ]

        response = self.client.post(
            f"/api/v1/coach/conversations/{conversation.id}/messages/stream",
            {"content": "Wait for it."},
            format="json",
            HTTP_ACCEPT="text/event-stream",
        )
        response = cast(StreamingHttpResponse, response)
        body = async_to_sync(_collect_stream)(response).decode()

        self.assertIn(": keepalive\n\n", body)
        self.assertIn("event: completed", body)

    def test_deleting_conversation_stales_pending_operations_but_preserves_ledger(
        self,
    ) -> None:
        """Deleting chat history preserves and stales the related recommendation ledger."""

        conversation = CoachConversation.objects.create(user=self.user)
        message = CoachMessage.objects.create(
            conversation=conversation, role="assistant", content="Change it."
        )
        recommendation = Recommendation.objects.create(
            user=self.user, conversation=conversation, coach_message=message
        )
        operation = RecommendationOperation.objects.create(
            recommendation=recommendation,
            operation_type="update_workout",
            payload={"workout_id": str(uuid.uuid4()), "changes": {"name": "Easy"}},
        )

        response = self.client.delete(f"/api/v1/coach/conversations/{conversation.id}")

        self.assertEqual(response.status_code, 204)
        operation.refresh_from_db()
        recommendation.refresh_from_db()
        self.assertEqual(operation.status, RecommendationOperation.Status.STALE)
        self.assertIsNotNone(operation.resolved_at)
        self.assertIsNone(recommendation.conversation_id)


def _parse_events(body: str) -> list[dict[str, Any]]:
    """Converts SSE test output into the owned event representation."""

    result: list[dict[str, Any]] = []
    for chunk in body.strip().split("\n\n"):
        if chunk.startswith(":"):
            continue
        lines = chunk.splitlines()
        result.append(
            {
                "event": lines[0].removeprefix("event: "),
                "data": json.loads(lines[1].removeprefix("data: ")),
            }
        )
    return result
