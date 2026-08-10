"""Tests for the Pydantic Coach adapter's private-history boundary."""

from __future__ import annotations

import uuid
from decimal import Decimal
from threading import enumerate as enumerate_threads
from types import SimpleNamespace
from unittest.mock import patch

from asgiref.sync import async_to_sync
from django.test import SimpleTestCase, override_settings
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from ai.implementations.pydantic_coach.contracts import (
    CoachDeps,
    CoachResponse,
    CoachRuntimeLimits,
)
from ai.implementations.pydantic_coach.runner import (
    PydanticCoachRunner,
    _restore_history,
    create_pydantic_coach_runner,
)
from ai.runner import CoachRunRequest, RunCompleted, TextDelta


async def _collect_events(runner: PydanticCoachRunner, request: CoachRunRequest) -> list[object]:
    return [event async for event in runner.stream(request)]


def _limits(*, history_max_batches: int = 12) -> CoachRuntimeLimits:
    return CoachRuntimeLimits(
        history_max_batches=history_max_batches,
        history_max_tokens=20_000,
        request_limit=6,
        tool_calls_limit=12,
        input_tokens_limit=24_000,
        output_tokens_limit=1_200,
        per_request_input_tokens_limit=20_000,
        cost_limit_usd=Decimal("0.05"),
        tool_timeout_seconds=10,
    )


class PydanticCoachRunnerTests(SimpleTestCase):
    def test_restore_history_keeps_only_the_configured_recent_batches(self) -> None:
        from pydantic_ai.messages import (
            ModelMessagesTypeAdapter,
            ModelRequest,
            UserPromptPart,
        )

        first = ModelMessagesTypeAdapter.dump_python(
            [ModelRequest(parts=[UserPromptPart(content="first")])], mode="json"
        )
        second = ModelMessagesTypeAdapter.dump_python(
            [ModelRequest(parts=[UserPromptPart(content="second")])], mode="json"
        )

        history = _restore_history([first, second], _limits(history_max_batches=1))

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].parts[0].content, "second")

    @override_settings(
        OPENAI_MODEL="gpt-4.1-mini",
        OPENAI_TIMEOUT=30,
        COACH_HISTORY_MAX_BATCHES=12,
        COACH_HISTORY_MAX_TOKENS=20_000,
        COACH_MAX_MODEL_REQUESTS=6,
        COACH_MAX_TOOL_CALLS=12,
        COACH_MAX_INPUT_TOKENS=24_000,
        COACH_MAX_OUTPUT_TOKENS=1_200,
        COACH_MAX_INPUT_TOKENS_PER_REQUEST=20_000,
        COACH_MAX_COST_USD="0.05",
        COACH_TOOL_TIMEOUT_SECONDS=10,
        COACH_LOGFIRE_ENABLED=False,
    )
    def test_factory_builds_the_sync_runner_without_resolving_a_live_model(self) -> None:
        runner = create_pydantic_coach_runner()

        self.assertIsInstance(runner, PydanticCoachRunner)
        self.assertEqual(runner._model_name, "gpt-4.1-mini")

    def test_structured_agent_output_maps_to_text_then_completed_event(self) -> None:
        agent = Agent(
            TestModel(
                custom_output_args={"content": "Keep the session easy.", "outcome": "insight"}
            ),
            deps_type=CoachDeps,
            output_type=CoachResponse,
        )
        user = object()
        conversation = object()
        user_model = SimpleNamespace(objects=SimpleNamespace(get=lambda **kwargs: user))
        conversations = SimpleNamespace(get=lambda **kwargs: conversation)
        request = CoachRunRequest(
            run_id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            content="What should I do today?",
            ai_message_batches=[],
        )
        runner = PydanticCoachRunner(limits=_limits(), model_name="unused", timeout_seconds=5)

        with (
            patch("ai.implementations.pydantic_coach.runner.create_coach_agent", return_value=agent),
            patch("ai.implementations.pydantic_coach.runner.get_user_model", return_value=user_model),
            patch("ai.implementations.pydantic_coach.runner.CoachConversation.objects", conversations),
        ):
            events = async_to_sync(_collect_events)(runner, request)
            thread_names_after = {thread.name for thread in enumerate_threads()}

        self.assertTrue(any(event == TextDelta(delta="Keep the session easy.") for event in events))
        self.assertNotIn("pydantic-coach-run", thread_names_after)
        completed = events[-1]
        self.assertIsInstance(completed, RunCompleted)
        assert isinstance(completed, RunCompleted)
        self.assertEqual(completed.result.content, "Keep the session easy.")
