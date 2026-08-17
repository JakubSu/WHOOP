"""Focused tests for Pydantic Coach construction and private contracts."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.test import SimpleTestCase
from pydantic_ai.models.test import TestModel

from ai.implementations.pydantic_coach.agent import create_coach_agent
from ai.implementations.pydantic_coach.contracts import (
    CoachDeps,
    CoachRunState,
    CoachRuntimeLimits,
)


class PydanticCoachAgentTests(SimpleTestCase):
    def test_agent_has_a_stable_observable_name_and_text_output(self) -> None:
        agent = create_coach_agent(model_name="gpt-5.6-luna", tool_timeout_seconds=10)

        self.assertEqual(agent.name, "whoop_coach")
        self.assertIs(agent.output_type, str)
        self.assertEqual(len(agent.toolsets), 1)

    def test_runtime_limits_reject_unbounded_or_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            CoachRuntimeLimits(
                recent_turns=0,
                context_token_reserve=4_000,
                request_limit=6,
                tool_calls_limit=12,
                input_tokens_limit=24_000,
                output_tokens_limit=1_200,
                per_request_input_tokens_limit=20_000,
                cost_limit_usd=Decimal("0.05"),
                tool_timeout_seconds=10,
            )

    def test_text_output_is_validated_with_pydantic_ais_test_model(self) -> None:
        agent = create_coach_agent(model_name="gpt-5.6-luna", tool_timeout_seconds=10)
        limits = CoachRuntimeLimits(
            recent_turns=4,
            context_token_reserve=4_000,
            request_limit=6,
            tool_calls_limit=12,
            input_tokens_limit=24_000,
            output_tokens_limit=1_200,
            per_request_input_tokens_limit=20_000,
            cost_limit_usd=Decimal("0.05"),
            tool_timeout_seconds=10,
        )
        deps = CoachDeps(
            user=object(),
            conversation=object(),
            run_id=uuid.uuid4(),
            limits=limits,
            state=CoachRunState(activity_sink=lambda activity: None),
        )
        model = TestModel(
            call_tools=[],
            custom_output_text="Keep today easy.",
        )

        with agent.override(model=model):
            result = agent.run_sync("Should I train?", deps=deps)

        self.assertEqual(result.output, "Keep today easy.")
