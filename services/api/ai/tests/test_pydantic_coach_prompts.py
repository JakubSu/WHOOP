"""Tests for the Coach's trusted tool-use guidance."""

from django.test import SimpleTestCase

from ai.implementations.pydantic_coach.prompts import COACH_INSTRUCTIONS


class CoachInstructionsTests(SimpleTestCase):
    def test_exercise_search_policy_requires_batched_name_lookups(self) -> None:
        self.assertIn("reuse results already returned in this run", COACH_INSTRUCTIONS)
        self.assertIn("multiple named exercises in one search_exercises call", COACH_INSTRUCTIONS)
        self.assertIn("Never invent exercise IDs.", COACH_INSTRUCTIONS)
