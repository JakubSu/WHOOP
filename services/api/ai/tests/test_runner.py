"""Tests for the framework-independent runner contract and Echo implementation."""

from __future__ import annotations

import uuid

from django.test import SimpleTestCase, override_settings

from ai.implementations.echo import EchoCoachRunner
from ai.runner import (
    CoachRunRequest,
    RunCompleted,
    TextDelta,
    ThinkingChanged,
    get_coach_runner,
)


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
            ai_message_batches=[[{"private": "history"}]],
        )

    def test_run_echoes_the_new_user_message(self) -> None:
        """The non-streaming path returns exactly the new user content."""

        result = get_coach_runner().run(self.request)

        self.assertEqual(result.content, "Repeat this.")
        self.assertEqual(result.ai_message_batch, [])

    def test_echo_implementation_is_separate_from_the_contract_module(self) -> None:
        """The concrete runner lives outside the runner contract module."""

        self.assertEqual(EchoCoachRunner.__module__, "ai.implementations.echo")

    def test_stream_emits_progress_text_and_a_completion(self) -> None:
        """The streaming path produces the normal owned runner event sequence."""

        events = list(get_coach_runner().stream(self.request))

        self.assertEqual(events[0], ThinkingChanged(active=True))
        self.assertEqual(events[1], ThinkingChanged(active=False))
        self.assertEqual(events[2], TextDelta(delta="Repeat this."))
        completed = events[3]
        assert isinstance(completed, RunCompleted)
        self.assertEqual(completed.result.content, "Repeat this.")
