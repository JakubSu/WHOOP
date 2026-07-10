from typing import Any
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.coach.context import CoachContextBuilder
from ai.coach.orchestrator import CoachOrchestrator
from ai.coach.schemas import CoachTurnDraft
from ai.coach.ui_actions import AuthorizeUiActionService
from recommendation.models import Recommendation
from recommendation.services import RecommendationNotFound, RecommendationValidationError
from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise


class FakeCoachGenerator:
    def __init__(self, draft: CoachTurnDraft) -> None:
        self.draft = draft
        self.calls: list[dict[str, Any]] = []

    def generate(self, context: dict[str, Any]) -> CoachTurnDraft:
        self.calls.append(context)
        return self.draft


class CoachServiceTests(TestCase):
    user_id = "user-1"
    other_user_id = "user-2"

    def setUp(self) -> None:
        self.exercise = Exercise.objects.create(name="Bench Press", user_id=self.user_id)
        self.replacement = Exercise.objects.create(name="Goblet Squat", user_id="")
        self.workout = Workout.objects.create(name="Upper Body", user_id=self.user_id)
        self.workout_exercise = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=5,
            reps=5,
        )
        self.plan = TrainingPlan.objects.create(name="Base Plan", user_id=self.user_id)
        self.planned_workout = Workout.objects.create(
            name="Lower Body",
            user_id=self.user_id,
            plan=self.plan,
            date="2026-07-09",
        )

    def test_workout_context_rejects_another_users_workout(self) -> None:
        other_workout = Workout.objects.create(name="Other", user_id=self.other_user_id)

        with self.assertRaises(RecommendationNotFound):
            CoachContextBuilder().build(
                user_id=self.user_id,
                page_context={
                    "page_type": "workout",
                    "context_id": str(other_workout.id),
                },
            )

    @patch("whoop.services.create_summary_service")
    def test_workout_context_can_create_pending_coach_recommendation(
        self,
        summary_factory: MagicMock,
    ) -> None:
        summary_factory.return_value.execute.return_value = {"connected": True}
        draft = CoachTurnDraft.model_validate(
            {
                "answer": "Reduce volume.",
                "workout_patch": {
                    "summary": "Reduce volume.",
                    "operations": [
                        {
                            "op": "update_exercise",
                            "workout_exercise_id": str(self.workout_exercise.id),
                            "changes": {"sets": 3},
                        }
                    ],
                },
            }
        )

        result = CoachOrchestrator(generator=FakeCoachGenerator(draft)).run_turn(
            user_id=self.user_id,
            page_context={
                "page_type": "workout",
                "context_id": str(self.workout.id),
            },
            message="Make it easier.",
        )

        recommendation = result.recommendation
        if recommendation is None:
            self.fail("Expected coach turn to create a recommendation.")
        self.assertEqual(recommendation.status, Recommendation.Status.PENDING)
        self.assertEqual(recommendation.source, Recommendation.Source.COACH_CHAT)

    def test_training_plan_context_cannot_create_workout_patch_recommendation(self) -> None:
        draft = CoachTurnDraft.model_validate(
            {
                "answer": "Open the workout first.",
                "workout_patch": {
                    "summary": "Invalid from plan.",
                    "operations": [
                        {
                            "op": "update_exercise",
                            "workout_exercise_id": str(self.workout_exercise.id),
                            "changes": {"sets": 3},
                        }
                    ],
                },
            }
        )

        with self.assertRaises(RecommendationValidationError):
            CoachOrchestrator(generator=FakeCoachGenerator(draft)).run_turn(
                user_id=self.user_id,
                page_context={
                    "page_type": "training_plan",
                    "context_id": str(self.plan.id),
                },
                message="Make tomorrow easier.",
            )

    def test_unauthorized_navigation_actions_are_rejected(self) -> None:
        other_workout = Workout.objects.create(name="Other", user_id=self.other_user_id)

        actions = AuthorizeUiActionService().authorize(
            user_id=self.user_id,
            proposed_actions=[
                {
                    "type": "navigate",
                    "target": "workout",
                    "id": str(other_workout.id),
                }
            ],
        )

        self.assertEqual(actions, [])

    def test_authorized_workout_navigation_emits_backend_route(self) -> None:
        actions = AuthorizeUiActionService().authorize(
            user_id=self.user_id,
            proposed_actions=[
                {
                    "type": "navigate",
                    "target": "workout",
                    "id": str(self.workout.id),
                }
            ],
        )

        self.assertEqual(
            actions,
            [
                {
                    "type": "navigate",
                    "route": f"/workouts/{self.workout.id}",
                }
            ],
        )

    def test_pain_language_sets_safety_flag_without_changing_answer(self) -> None:
        draft = CoachTurnDraft(answer="Avoid movements that hurt and consider lowering load.")

        result = CoachOrchestrator(generator=FakeCoachGenerator(draft)).run_turn(
            user_id=self.user_id,
            page_context={
                "page_type": "workout",
                "context_id": str(self.workout.id),
            },
            message="My knee hurts during squats.",
        )

        self.assertEqual(result.answer, "Avoid movements that hurt and consider lowering load.")
        self.assertIn("pain_or_injury_mentioned", result.safety_flags)
