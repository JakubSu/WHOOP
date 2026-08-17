"""Regression tests for bounded Coach context and durable memory."""

from __future__ import annotations

import uuid
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.test import TestCase
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from ai.implementations.pydantic_coach.memory import (
    ConversationMemory,
    project_batch_for_prompt,
)
from ai.implementations.pydantic_coach.runner import PydanticCoachRunner
from ai.implementations.pydantic_coach.contracts import CoachRuntimeLimits
from coach.models import CoachConversation, CoachMessage


def _limits() -> CoachRuntimeLimits:
    return CoachRuntimeLimits(
        recent_turns=4,
        raw_history_tokens=6_000,
        summary_input_tokens=4_000,
        summary_output_tokens=500,
        request_limit=6,
        tool_calls_limit=12,
        input_tokens_limit=24_000,
        output_tokens_limit=1_200,
        per_request_input_tokens_limit=20_000,
        cost_limit_usd=Decimal("0.05"),
        tool_timeout_seconds=10,
    )


class PydanticCoachMemoryTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email="memory@example.com", password="strong-password"
        )
        self.conversation = CoachConversation.objects.create(user=self.user)

    def test_historical_tool_results_are_projected_without_changing_audit_batch(self) -> None:
        batch = [
            {
                "kind": "request",
                "parts": [
                    {
                        "part_kind": "tool-return",
                        "tool_name": "search_exercises",
                        "content": [
                            {"id": str(uuid.uuid4()), "name": f"Exercise {index}", "unused": "x"}
                            for index in range(10)
                        ],
                    }
                ],
            }
        ]

        projected, compacted = project_batch_for_prompt(batch)

        self.assertEqual(compacted, 1)
        self.assertEqual(len(batch[0]["parts"][0]["content"]), 10)
        compacted_content = projected[0]["parts"][0]["content"]
        self.assertEqual(len(compacted_content), 5)
        self.assertEqual(set(compacted_content[0]), {"id", "name"})

    def test_memory_cursor_advances_once_for_each_retired_turn(self) -> None:
        [
            CoachMessage.objects.create(
                conversation=self.conversation,
                role=CoachMessage.Role.ASSISTANT,
                content=f"Answer {index}",
                ai_message_batch=[{"turn": index}],
            )
            for index in range(5)
        ]
        retired = CoachMessage.objects.filter(conversation=self.conversation).order_by(
            "created_at", "id"
        )[0]
        runner = PydanticCoachRunner(
            limits=_limits(), model_name="unused", timeout_seconds=5
        )
        runner._memory_agent = Agent(
            TestModel(custom_output_args={"decisions": ["Keep the plan easy."]}),
            output_type=ConversationMemory,
        )

        async_to_sync(runner.maintain_memory)(
            conversation_id=self.conversation.id, user_id=self.user.id
        )
        self.conversation.refresh_from_db()

        self.assertEqual(self.conversation.memory_through_message_id, retired.id)
        self.assertEqual(self.conversation.memory["decisions"], ["Keep the plan easy."])

        async_to_sync(runner.maintain_memory)(
            conversation_id=self.conversation.id, user_id=self.user.id
        )
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.memory_through_message_id, retired.id)
