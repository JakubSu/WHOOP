from typing import Any
from unittest.mock import MagicMock, patch

from django.test import TestCase
from recommendation import services as recommendation_services
from training.models import Exercise, Workout, WorkoutExercise
from whoop.exceptions import WhoopConnectionNotFound

from ai.recommendation.schemas import WorkoutPatchDraft
from ai.recommendation.services import recommendation_tools


class FakeWorkoutPatchGenerator:
    def __init__(self, draft: WorkoutPatchDraft) -> None:
        self.draft = draft
        self.calls: list[dict[str, Any]] = []

    def generate(self, context: dict[str, Any]) -> WorkoutPatchDraft:
        self.calls.append({"context": context})
        return self.draft


class RecommendationToolTests(TestCase):
    user_id = "user-1"
    other_user_id = "user-2"

    def setUp(self) -> None:
        self.bench = Exercise.objects.create(name="Bench Press", user_id=self.user_id)
        self.goblet = Exercise.objects.create(name="Goblet Squat", user_id="")
        self.row = Exercise.objects.create(name="Row", user_id=self.user_id)
        self.workout = Workout.objects.create(
            name="Upper Body",
            date="2026-06-09",
            user_id=self.user_id,
        )
        self.bench_row = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.bench,
            sets=5,
            reps=5,
        )
        self.row_row = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.row,
            sets=3,
            reps=8,
        )
        self.bench_row_id = str(self.bench_row.id)

    def test_context_contains_workout_rows_and_available_exercises(self) -> None:
        context = recommendation_tools.build_workout_recommendation_context(
            self.user_id,
            str(self.workout.id),
        )

        self.assertEqual(context["current_workout"]["id"], str(self.workout.id))
        self.assertEqual(
            context["current_workout"]["exercises"][0]["workout_exercise_id"],
            self.bench_row_id,
        )
        self.assertIn(
            str(self.goblet.id),
            [exercise["id"] for exercise in context["available_exercises"]],
        )
        self.assertIn("whoop_summary", context)

    @patch("whoop.services.create_summary_service")
    def test_context_contains_connected_whoop_summary(
        self, summary_factory: MagicMock
    ) -> None:
        summary_factory.return_value.execute.return_value = {
            "connected": True,
            "recovery_score": 72.0,
            "recent_workouts": [{"id": "workout-id", "sport_name": "running"}],
        }

        context = recommendation_tools.build_workout_recommendation_context(
            self.user_id,
            str(self.workout.id),
        )

        summary_factory.return_value.execute.assert_called_once_with(self.user_id)
        self.assertTrue(context["whoop_summary"]["connected"])
        self.assertEqual(
            context["whoop_summary"]["recent_workouts"][0]["sport_name"], "running"
        )

    @patch("whoop.services.create_summary_service")
    def test_context_uses_disconnected_whoop_summary_when_whoop_is_not_connected(
        self,
        summary_factory: MagicMock,
    ) -> None:
        summary_factory.return_value.execute.side_effect = WhoopConnectionNotFound()

        context = recommendation_tools.build_workout_recommendation_context(
            self.user_id,
            str(self.workout.id),
        )

        self.assertFalse(context["whoop_summary"]["connected"])

    def test_generate_stores_single_domain_operation_from_mocked_provider(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Reduce fatigue.",
                "reason": "Recovery is low.",
                "operation": {
                    "op": "update_exercise",
                    "workout_exercise_id": self.bench_row_id,
                    "changes": {"sets": 3},
                },
            }
        )
        generator = FakeWorkoutPatchGenerator(draft)

        recommendation = recommendation_tools.generate_recommendation_for_workout(
            self.user_id,
            str(self.workout.id),
            generator=generator,
        )

        self.assertEqual(recommendation.summary, "Reduce fatigue.")
        self.assertEqual(recommendation.operation_type, "update_exercise")
        self.assertEqual(recommendation.payload_json["changes"], {"sets": 3})
        self.assertEqual(
            generator.calls[0]["context"]["current_workout"]["id"],
            str(self.workout.id),
        )

    def test_generate_rejects_other_users_workout_exercise(self) -> None:
        other_workout = Workout.objects.create(
            name="Other",
            date="2026-06-09",
            user_id=self.other_user_id,
        )
        other_workout_exercise = WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=self.goblet,
        )
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Invalid.",
                "operation": {
                    "op": "remove_exercise",
                    "workout_exercise_id": str(other_workout_exercise.id),
                },
            }
        )

        with self.assertRaises(recommendation_services.RecommendationValidationError):
            recommendation_tools.generate_recommendation_for_workout(
                self.user_id,
                str(self.workout.id),
                generator=FakeWorkoutPatchGenerator(draft),
            )

    def test_generate_ignores_noop_time_change_for_strength_exercise(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Reduce fatigue.",
                "operation": {
                    "op": "update_exercise",
                    "workout_exercise_id": self.bench_row_id,
                    "changes": {"sets": 3, "reps": 6, "time": 0},
                },
            }
        )

        recommendation = recommendation_tools.generate_recommendation_for_workout(
            self.user_id,
            str(self.workout.id),
            generator=FakeWorkoutPatchGenerator(draft),
        )

        self.assertEqual(recommendation.payload_json["changes"], {"sets": 3, "reps": 6})

    def test_generate_rejects_positive_time_change_for_strength_exercise(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Invalid.",
                "operation": {
                    "op": "update_exercise",
                    "workout_exercise_id": self.bench_row_id,
                    "changes": {"time": 30},
                },
            }
        )

        with self.assertRaises(recommendation_services.RecommendationValidationError):
            recommendation_tools.generate_recommendation_for_workout(
                self.user_id,
                str(self.workout.id),
                generator=FakeWorkoutPatchGenerator(draft),
            )
