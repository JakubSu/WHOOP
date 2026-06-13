from django.test import SimpleTestCase
from pydantic import ValidationError

from recommendation.schemas import WorkoutRecommendationResponse


class WorkoutRecommendationSchemaTests(SimpleTestCase):
    def test_accepts_valid_operations(self) -> None:
        response = WorkoutRecommendationResponse.model_validate(
            {
                "summary": "Reduce fatigue.",
                "operations": [
                    {
                        "op": "replace_exercise",
                        "workout_exercise_id": "workout-exercise-1",
                        "replacement_exercise_id": "exercise-2",
                    },
                    {
                        "op": "update_exercise",
                        "workout_exercise_id": "workout-exercise-2",
                        "changes": {"sets": 3, "reps": 5},
                    },
                    {
                        "op": "remove_exercise",
                        "workout_exercise_id": "workout-exercise-3",
                    },
                    {
                        "op": "add_exercise",
                        "exercise_id": "exercise-4",
                        "sets": 2,
                        "weight": 25,
                        "weight_unit": "lb",
                    },
                ],
            }
        )

        self.assertEqual(len(response.operations), 4)

    def test_rejects_invalid_operation_type(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operations": [{"op": "rename_exercise", "name": "Invented"}],
                }
            )

    def test_rejects_effort_field(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operations": [
                        {
                            "op": "update_exercise",
                            "workout_exercise_id": "workout-exercise-1",
                            "changes": {"effort": "hard"},
                        }
                    ],
                }
            )

    def test_rejects_unsupported_update_field(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operations": [
                        {
                            "op": "update_exercise",
                            "workout_exercise_id": "workout-exercise-1",
                            "changes": {"rpe": 6},
                        }
                    ],
                }
            )

    def test_rejects_empty_update_changes(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operations": [
                        {
                            "op": "update_exercise",
                            "workout_exercise_id": "workout-exercise-1",
                            "changes": {},
                        }
                    ],
                }
            )
