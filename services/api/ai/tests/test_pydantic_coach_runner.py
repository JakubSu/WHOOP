"""Tests for the provider-counted Coach context composer."""

from __future__ import annotations

from dataclasses import dataclass

from django.test import SimpleTestCase
from pydantic_ai import UsageLimitExceeded
from pydantic_ai.messages import ModelRequest, UserPromptPart

from ai.implementations.pydantic_coach.history import select_context
from ai.implementations.pydantic_coach.runner import _usage_limit_failure_code
from ai.runner import CoachConversationHistory, CoachHistoryTurn


@dataclass
class MessageEstimate:
    """Deterministic stand-in for the provider token-count endpoint."""

    limit_per_message: int = 10

    def __call__(self, messages: list[object]) -> int:
        return len(messages) * self.limit_per_message


class ContextComposerTests(SimpleTestCase):
    def _select(self, history: CoachConversationHistory, limit: int):
        return select_context(
            history=history,
            base_messages=[ModelRequest(parts=[UserPromptPart(content="new request")])],
            token_limit=limit,
            estimate=MessageEstimate(),
        )

    def test_prefers_the_newest_raw_turn_when_it_fits(self) -> None:
        raw = [
            {
                "kind": "request",
                "parts": [{"part_kind": "user-prompt", "content": "raw"}],
            }
        ]
        selection = self._select(
            CoachConversationHistory(
                turns=[CoachHistoryTurn("user", "visible", raw_batch=raw)]
            ),
            limit=20,
        )

        self.assertEqual(selection.raw_turn_count, 1)
        self.assertEqual(selection.visible_turn_count, 0)
        self.assertEqual(selection.messages[0].parts[0].content, "raw")

    def test_falls_back_to_visible_text_for_an_oversized_raw_turn(self) -> None:
        raw = [
            {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "one"}]},
            {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "two"}]},
            {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "three"}]},
        ]
        selection = self._select(
            CoachConversationHistory(
                turns=[CoachHistoryTurn("user", "visible", raw_batch=raw)]
            ),
            limit=30,
        )

        self.assertEqual(selection.raw_turn_count, 0)
        self.assertEqual(selection.visible_turn_count, 1)
        self.assertEqual(selection.messages[0].parts[0].content, "user")
        self.assertEqual(selection.messages[1].parts[0].content, "visible")

    def test_stops_before_the_first_turn_whose_visible_form_does_not_fit(self) -> None:
        selection = self._select(
            CoachConversationHistory(
                turns=[
                    CoachHistoryTurn("old", "old reply"),
                    CoachHistoryTurn("new", "new reply"),
                ]
            ),
            limit=30,
        )

        self.assertEqual(selection.visible_turn_count, 1)
        self.assertEqual(selection.dropped_turn_count, 1)
        self.assertEqual(selection.messages[0].parts[0].content, "new")


class UsageLimitFailureCodeTests(SimpleTestCase):
    def test_classifies_each_configured_usage_limit(self) -> None:
        cases = {
            "per_request_input_tokens_limit": "context_limit",
            "input_tokens_limit": "input_token_limit",
            "output_tokens_limit": "output_token_limit",
            "tool_calls_limit": "tool_call_limit",
            "request_limit": "request_limit",
            "cost_limit": "cost_limit",
        }

        for limit_name, expected_code in cases.items():
            with self.subTest(limit_name=limit_name):
                error = UsageLimitExceeded(f"Exceeded the {limit_name} of 1")
                self.assertEqual(_usage_limit_failure_code(error), expected_code)
