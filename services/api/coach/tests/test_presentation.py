from django.test import SimpleTestCase

from coach.presentation import TOOL_PRESENTATIONS, safe_activity_presentation


class CoachActivityPresentationTests(SimpleTestCase):
    def test_every_registered_coach_tool_has_a_specific_safe_presentation(self) -> None:
        expected_tools = {
            "search_workouts",
            "get_workout",
            "get_whoop_summary",
            "search_exercises",
            "get_exercise",
            "request_ui_action",
            "get_active_recommendation",
            "create_recommendation",
        }

        self.assertEqual(set(TOOL_PRESENTATIONS), expected_tools)
        for tool_name in expected_tools:
            kind, label = safe_activity_presentation("other", tool_name)
            self.assertNotEqual(kind, "other")
            self.assertNotEqual(label, "Working on your request…")

    def test_unknown_tool_uses_a_safe_generic_presentation(self) -> None:
        self.assertEqual(
            safe_activity_presentation("unknown", "unrecognized_tool"),
            ("other", "Working on your request…"),
        )
