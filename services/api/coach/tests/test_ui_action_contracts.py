"""Tests for Coach-owned UI action contracts."""

from django.test import SimpleTestCase
from pydantic import ValidationError

from coach.contracts.ui_actions import ExerciseResolutionUiActionDraft


class UiActionContractTests(SimpleTestCase):
    def test_exercise_resolution_action_draft_is_typed_and_serializable(self) -> None:
        action = ExerciseResolutionUiActionDraft.model_validate(
            {
                "type": "exercise_resolution",
                "payload": {
                    "requested_name": " Landmine press ",
                    "draft_exercise": {
                        "name": " Landmine press ",
                        "prescription_type": "strength",
                        "muscle_group": "shoulders",
                        "default_sets": 3,
                        "default_reps": 10,
                        "default_time": 0,
                        "notes": "",
                    },
                },
            }
        )

        self.assertEqual(
            action.model_dump(mode="json")["payload"]["requested_name"],
            "Landmine press",
        )
        with self.assertRaises(ValidationError):
            ExerciseResolutionUiActionDraft.model_validate(
                {
                    "type": "exercise_resolution",
                    "payload": {
                        "requested_name": "Landmine press",
                        "draft_exercise": {
                            "name": "Landmine press",
                            "prescription_type": "unsupported",
                            "muscle_group": "shoulders",
                        },
                    },
                }
            )
