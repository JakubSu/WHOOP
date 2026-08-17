"""Tests for the framework-independent runner contract and Echo implementation."""

from __future__ import annotations

import uuid
from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import SimpleTestCase, override_settings

from ai.implementations.echo import EchoCoachRunner
from ai.runner import (
    CoachConversationHistory,
    CoachHistoryTurn,
    CoachRunRequest,
    RunCompleted,
    TextDelta,
    ThinkingChanged,
    get_coach_runner,
    initialize_coach_runner,
)


async def _collect_events(runner: object, request: CoachRunRequest) -> list[object]:
    return [event async for event in runner.stream(request)]  # type: ignore[attr-defined]


@override_settings(
    COACH_RUNNER_FACTORY="ai.implementations.echo.create_echo_runner",
    COACH_ECHO_THINK_SECONDS=0,
)
class EchoCoachRunnerTests(SimpleTestCase):
    """Verifies the development runner exercises the owned coach contracts."""

    def setUp(self) -> None:
        """Builds a representative request containing new content and private history."""

        self.request = CoachRunRequest(
            run_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            content="Repeat this.",
            history=CoachConversationHistory(
                turns=[CoachHistoryTurn("", "", raw_batch=[{"private": "history"}])],
            ),
        )

    def test_run_echoes_the_new_user_message(self) -> None:
        """The non-streaming path returns exactly the new user content."""

        result = async_to_sync(get_coach_runner().run)(self.request)

        self.assertEqual(result.content, "Repeat this.")
        self.assertEqual(result.ai_message_batch, [])

    def test_echo_implementation_is_separate_from_the_contract_module(self) -> None:
        """The concrete runner lives outside the runner contract module."""

        self.assertEqual(EchoCoachRunner.__module__, "ai.implementations.echo")

    def test_stream_emits_progress_text_and_a_completion(self) -> None:
        """The streaming path produces the normal owned runner event sequence."""

        events = async_to_sync(_collect_events)(get_coach_runner(), self.request)

        self.assertEqual(events[0], ThinkingChanged(active=True))
        self.assertEqual(events[1], ThinkingChanged(active=False))
        self.assertEqual(events[2], TextDelta(delta="Repeat this."))
        completed = events[3]
        assert isinstance(completed, RunCompleted)
        self.assertEqual(completed.result.content, "Repeat this.")

    def test_initialized_runner_is_reused_by_requests(self) -> None:
        """Startup construction prevents subsequent requests rebuilding the runner."""

        with patch("ai.runner._startup_coach_runner", None):
            initialized = initialize_coach_runner()

            self.assertIs(get_coach_runner(), initialized)
