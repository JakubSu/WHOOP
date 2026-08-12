"""Tests for framework-independent AI tools and recommendation safety boundaries."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any, cast
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ai.tools import (
    CoachToolContext,
    create_recommendation,
    get_active_recommendation,
    get_whoop_summary,
    get_workout,
    search_exercises,
    search_workouts,
)
from ai.tools.errors import ToolNotFoundError, ToolValidationError
from coach.models import CoachConversation
from recommendation.contracts import RecommendationDraft
from recommendation.models import Recommendation, RecommendationOperation
from recommendation.services import expire_run_recommendations
from training.models import Exercise, Workout
from whoop.exceptions import WhoopConnectionNotFound


class CoachToolTests(TestCase):
    """Verifies AI tools preserve authenticated ownership and ledger safety."""

    def setUp(self) -> None:
        """Creates independent users, conversations, and scoped training records."""

        user_model = get_user_model()
        self.user = cast(Any, user_model.objects).create_user(
            email="coach-tools@example.com", password="strong-password"
        )
        self.other_user = cast(Any, user_model.objects).create_user(
            email="other-tools@example.com", password="strong-password"
        )
        self.conversation = CoachConversation.objects.create(user=self.user)
        self.run_id = uuid.uuid4()
        self.workout = Workout.objects.create(
            user_id=str(self.user.id), name="Tempo run", date=date(2026, 8, 5)
        )
        self.other_workout = Workout.objects.create(
            user_id=str(self.other_user.id), name="Private run", date=date(2026, 8, 5)
        )

    def context(self, *, tool_call_id: str = "call-1") -> CoachToolContext:
        """Builds an authenticated context for one recommendation tool call."""

        return CoachToolContext(
            user=self.user,
            conversation=self.conversation,
            run_id=self.run_id,
            tool_call_id=tool_call_id,
        )

    def draft(self, workout_id: uuid.UUID) -> RecommendationDraft:
        """Builds a valid user-owned workout update recommendation."""

        return RecommendationDraft.model_validate(
            {
                "summary": "Reduce volume",
                "operations": [
                    {
                        "operation_type": "update_workout",
                        "reason": "Keep the session manageable.",
                        "payload": {
                            "workout_id": str(workout_id),
                            "changes": {"name": "Easy session"},
                        },
                    }
                ],
            }
        )

    def test_create_recommendation_returns_an_existing_id_idempotently(self) -> None:
        """A repeated framework retry returns one user-owned recommendation ledger."""

        first = create_recommendation(self.context(), draft=self.draft(self.workout.id))
        second = create_recommendation(
            self.context(), draft=self.draft(self.workout.id)
        )

        self.assertEqual(first.recommendation_id, second.recommendation_id)
        recommendation = Recommendation.objects.get(pk=first.recommendation_id)
        self.assertEqual(recommendation.conversation, self.conversation)
        self.assertIsNone(recommendation.coach_message)
        self.assertEqual(recommendation.status, Recommendation.Status.ACTIVE)

    def test_create_recommendation_rejects_another_users_target(self) -> None:
        """The write tool cannot propose an operation against another user's workout."""

        with self.assertRaises(ToolValidationError):
            create_recommendation(
                self.context(), draft=self.draft(self.other_workout.id)
            )

    def test_create_recommendation_replaces_the_complete_active_proposal(self) -> None:
        """The write tool stales prior pending work but preserves a proposal ledger."""

        original = create_recommendation(
            self.context(tool_call_id="original"), draft=self.draft(self.workout.id)
        )
        replacement = RecommendationDraft.model_validate(
            {
                "summary": "Reduce volume further",
                "operations": [
                    {
                        "operation_type": "update_workout",
                        "reason": "Keep the session manageable.",
                        "payload": {
                            "workout_id": str(self.workout.id),
                            "changes": {"name": "Recovery session"},
                        },
                    }
                ],
            }
        )

        replacement_result = create_recommendation(
            CoachToolContext(
                user=self.user,
                conversation=self.conversation,
                run_id=uuid.uuid4(),
                tool_call_id="replacement",
            ),
            draft=replacement,
            replaces_recommendation_id=str(original.recommendation_id),
        )

        original_recommendation = Recommendation.objects.get(
            pk=original.recommendation_id
        )
        original_operation = RecommendationOperation.objects.get(
            recommendation=original_recommendation
        )
        self.assertEqual(
            original_recommendation.status, Recommendation.Status.SUPERSEDED
        )
        self.assertEqual(
            original_recommendation.replaced_by_id,
            replacement_result.recommendation_id,
        )
        self.assertEqual(
            original_operation.status, RecommendationOperation.Status.STALE
        )
        active = get_active_recommendation(self.context(tool_call_id="read"))
        self.assertIsNotNone(active)
        if active is not None:
            self.assertEqual(
                active.recommendation_id, replacement_result.recommendation_id
            )
            self.assertEqual(active.draft.summary, "Reduce volume further")

    def test_read_tools_return_only_user_scoped_records(self) -> None:
        """Workout and exercise tools enforce ownership and safe shared-library visibility."""

        shared = Exercise.objects.create(
            name="Shared squat", muscle_group=Exercise.MuscleGroup.QUADS
        )
        private = Exercise.objects.create(
            user_id=str(self.user.id),
            name="Private row",
            muscle_group=Exercise.MuscleGroup.BACK,
        )
        Exercise.objects.create(
            user_id=str(self.other_user.id),
            name="Other lift",
            muscle_group=Exercise.MuscleGroup.BACK,
        )

        workouts = search_workouts(self.context(), limit=1000)
        exercises = search_exercises(self.context(), query="", limit=1000)

        self.assertEqual([item.id for item in workouts], [self.workout.id])
        exercise_ids = {item.id for item in exercises}
        self.assertTrue({shared.id, private.id}.issubset(exercise_ids))
        self.assertNotIn(
            Exercise.objects.get(user_id=str(self.other_user.id), name="Other lift").id,
            exercise_ids,
        )
        with self.assertRaises(ToolNotFoundError):
            get_workout(self.context(), workout_id=self.other_workout.id)

    def test_exercise_search_matches_any_requested_muscle_group(self) -> None:
        """The tool combines name search with an any-of muscle-group filter."""

        chest = Exercise.objects.create(
            name="Chest press", muscle_group=Exercise.MuscleGroup.CHEST
        )
        triceps = Exercise.objects.create(
            name="Triceps press", muscle_group=Exercise.MuscleGroup.TRICEPS
        )
        Exercise.objects.create(name="Back row", muscle_group=Exercise.MuscleGroup.BACK)

        exercises = search_exercises(
            self.context(),
            query="press",
            muscle_groups=[
                Exercise.MuscleGroup.CHEST,
                Exercise.MuscleGroup.TRICEPS,
            ],
        )

        exercise_ids = {item.id for item in exercises}
        self.assertTrue({chest.id, triceps.id}.issubset(exercise_ids))
        self.assertNotIn(
            Exercise.objects.get(name="Back row").id,
            exercise_ids,
        )

    @patch("ai.tools.recovery.services.create_summary_service")
    def test_whoop_summary_uses_the_whoop_summary_service(
        self, create_summary_service: Any
    ) -> None:
        """The tool delegates cache and refresh policy to the WHOOP context."""

        create_summary_service.return_value.execute.return_value = {
            "connected": True,
            "snapshot_date": "2026-08-06",
            "recovery_score": 72.0,
            "sleep_performance_percent": 85.0,
            "day_strain": 10.5,
            "hrv_rmssd_milli": 55.0,
            "resting_heart_rate": 48.0,
            "sleep_duration_minutes": 420,
            "recent_workout_count": 2,
            "recent_workouts": [],
            "refreshed_at": "2026-08-06T12:00:00Z",
        }

        summary = get_whoop_summary(self.context())

        create_summary_service.return_value.execute.assert_called_once_with(
            str(self.user.id)
        )
        if summary is None:
            self.fail("Expected a normalized WHOOP summary.")
        self.assertEqual(summary.recovery_score, 72.0)

    @patch("ai.tools.recovery.services.create_summary_service")
    def test_whoop_summary_returns_none_when_whoop_is_not_connected(
        self, create_summary_service: Any
    ) -> None:
        """The tool preserves its optional result when no WHOOP account exists."""

        create_summary_service.return_value.execute.side_effect = (
            WhoopConnectionNotFound
        )

        self.assertIsNone(get_whoop_summary(self.context()))

    def test_expiring_a_failed_run_preserves_the_ledger(self) -> None:
        """A failed run expires its recommendations and stales only pending operations."""

        created = create_recommendation(
            self.context(), draft=self.draft(self.workout.id)
        )

        expired_count = expire_run_recommendations(user=self.user, run_id=self.run_id)

        recommendation = Recommendation.objects.get(pk=created.recommendation_id)
        operation = RecommendationOperation.objects.get(recommendation=recommendation)
        self.assertEqual(expired_count, 1)
        self.assertEqual(recommendation.status, Recommendation.Status.EXPIRED)
        self.assertIsNotNone(recommendation.expired_at)
        self.assertEqual(operation.status, RecommendationOperation.Status.STALE)
