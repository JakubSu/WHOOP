"""Tests for the saved Coach-token analysis command."""

from django.test import SimpleTestCase

from coach.management.commands.analyze_turn_tokens import (
    _context_input_estimate,
    _current_run_input_tokens,
    _encoding_for,
    _json_tokens,
    _provider_request_inputs,
    _raw_batch_categories,
    _tool_activity,
)
from ai.runner import CoachHistoryTurn


class AnalyzeTurnTokensTests(SimpleTestCase):
    def test_raw_batch_is_split_into_message_categories(self) -> None:
        categories = _raw_batch_categories(
            _encoding_for("gpt-5.6-luna"),
            [
                {
                    "kind": "request",
                    "parts": [
                        {"part_kind": "user-prompt", "content": "Change my workout"},
                        {
                            "part_kind": "tool-return",
                            "tool_name": "get_workout",
                            "content": '{"name":"Lower Push"}',
                        },
                    ],
                },
                {
                    "kind": "response",
                    "parts": [
                        {"part_kind": "thinking", "content": ""},
                        {
                            "part_kind": "tool-call",
                            "tool_name": "get_workout",
                            "args": '{"workout_id":"abc"}',
                        },
                        {"part_kind": "text", "content": "I found it."},
                    ],
                },
            ],
        )

        self.assertGreater(categories["raw_user_prompt_tokens"], 0)
        self.assertGreater(categories["raw_assistant_text_tokens"], 0)
        self.assertGreater(categories["raw_tool_call_tokens"], 0)
        self.assertGreater(categories["raw_tool_result_tokens"], 0)
        self.assertGreaterEqual(categories["raw_protocol_tokens"], 0)
        self.assertEqual(
            categories["raw_context_tokens"],
            sum(value for key, value in categories.items() if key != "raw_context_tokens"),
        )

    def test_tool_activity_counts_parallel_calls_as_one_round(self) -> None:
        activity = _tool_activity(
            [
                {
                    "kind": "response",
                    "parts": [
                        {"part_kind": "tool-call", "tool_name": "get_workout"},
                        {"part_kind": "tool-call", "tool_name": "search_workouts"},
                    ],
                },
                {
                    "kind": "request",
                    "parts": [{"part_kind": "tool-return", "tool_name": "get_workout"}],
                },
                {
                    "kind": "response",
                    "parts": [{"part_kind": "tool-call", "tool_name": "create_plan"}],
                },
            ]
        )

        self.assertEqual(activity, {"tool_call_count": 3, "tool_round_count": 2})

    def test_current_run_inputs_grow_for_each_model_request(self) -> None:
        encoding = _encoding_for("gpt-5.6-luna")
        batch = [
            {"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "Hi"}]},
            {"kind": "response", "parts": [{"part_kind": "tool-call", "tool_name": "lookup"}]},
            {"kind": "request", "parts": [{"part_kind": "tool-return", "content": "found"}]},
            {"kind": "response", "parts": [{"part_kind": "text", "content": "Done"}]},
        ]

        tokens, request_count = _current_run_input_tokens(encoding, batch, user_tokens=1)

        self.assertEqual(request_count, 2)
        self.assertEqual(
            tokens,
            _json_tokens(encoding, batch[:1]) + _json_tokens(encoding, batch[:3]),
        )

    def test_provider_input_usage_is_taken_from_saved_responses(self) -> None:
        inputs = _provider_request_inputs(
            [
                {"kind": "request", "parts": []},
                {"kind": "response", "usage": {"input_tokens": 4_662}},
                {"kind": "response", "usage": {"input_tokens": 5_133}},
            ]
        )

        self.assertEqual(inputs, [4_662, 5_133])

    def test_context_estimate_includes_the_current_user_message(self) -> None:
        estimate = _context_input_estimate(
            [CoachHistoryTurn(user_content="Earlier question", assistant_content="Earlier answer")],
            "New question",
        )

        self.assertIsInstance(estimate, int)
        self.assertGreater(estimate, 0)
