"""Tests for the Coach's trusted tool-use guidance."""

from django.test import SimpleTestCase

from ai.implementations.pydantic_coach.prompts import COACH_INSTRUCTIONS


class CoachInstructionsTests(SimpleTestCase):
    def test_exercise_search_policy_requires_batched_name_lookups(self) -> None:
        self.assertIn("reuse results already returned in this run", COACH_INSTRUCTIONS)
        self.assertIn("multiple named exercises in one search_exercises call", COACH_INSTRUCTIONS)
        self.assertIn("Never invent exercise IDs.", COACH_INSTRUCTIONS)
        self.assertIn("When calling `request_ui_action`, keep that response to one short", COACH_INSTRUCTIONS)

    def test_response_format_is_universal_markdown(self) -> None:
        self.assertIn("Every final response must use GitHub-flavored Markdown.", COACH_INSTRUCTIONS)
        self.assertIn("This response format applies to every final response", COACH_INSTRUCTIONS)
