from django.test import SimpleTestCase
from pydantic import ValidationError

from recommendation.schemas import WorkoutRecommendationResponse


class WorkoutRecommendationSchemaTests(SimpleTestCase):
    def test_accepts_valid_operation(self) -> None:
        response = WorkoutRecommendationResponse.model_validate(
            {
                "summary": "Reduce fatigue.",
                "operation": {
                    "op": "update_exercise",
                    "workout_exercise_id": "workout-exercise-2",
                    "changes": {"sets": 3, "reps": 5},
                },
            }
        )

        self.assertEqual(response.operation.op, "update_exercise")

    def test_accepts_domain_workout_operation(self) -> None:
        response = WorkoutRecommendationResponse.model_validate(
            {
                "summary": "Redesign the workout.",
                "operation": {
                    "op": "revise_workout",
                    "workout_id": "workout-1",
                    "proposed_workout": {
                        "name": "Lower stress lift",
                        "date": "2026-06-10",
                        "goal": "Reduce fatigue",
                        "notes": "Keep it easy.",
                        "exercises": [
                            {
                                "exercise_definition_id": "exercise-1",
                                "sets": 2,
                                "reps": 8,
                                "weight": 25,
                            }
                        ],
                    },
                },
            }
        )

        self.assertEqual(response.operation.op, "revise_workout")

    def test_rejects_invalid_operation_type(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operation": {"op": "rename_exercise", "name": "Invented"},
                }
            )

    def test_rejects_effort_field(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operation": {
                        "op": "update_exercise",
                        "workout_exercise_id": "workout-exercise-1",
                        "changes": {"effort": "hard"},
                    },
                }
            )

    def test_rejects_empty_update_changes(self) -> None:
        with self.assertRaises(ValidationError):
            WorkoutRecommendationResponse.model_validate(
                {
                    "summary": "Nope.",
                    "operation": {
                        "op": "update_exercise",
                        "workout_exercise_id": "workout-exercise-1",
                        "changes": {},
                    },
                }
            )
