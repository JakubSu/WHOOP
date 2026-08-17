from datetime import date
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase

from coach.view_context import (
    InvalidCoachViewContext,
    WeekViewContext,
    WorkoutViewContext,
    resolve_view_context,
)
from training.models import Workout


class CoachViewContextTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = cast(Any, user_model.objects).create_user(
            email="context-owner@example.com", password="strong-password"
        )
        self.other_user = cast(Any, user_model.objects).create_user(
            email="context-other@example.com", password="strong-password"
        )

    def test_resolves_only_an_owned_workout(self) -> None:
        workout = Workout.objects.create(
            user_id=str(self.user.id), name="Push", date=date(2026, 8, 10)
        )

        resolved = resolve_view_context(
            self.user, {"kind": "workout", "workout_id": workout.id}
        )

        self.assertIsInstance(resolved, WorkoutViewContext)
        assert isinstance(resolved, WorkoutViewContext)
        self.assertEqual(resolved.as_dict()["workout_id"], str(workout.id))
        with self.assertRaises(InvalidCoachViewContext):
            resolve_view_context(
                self.other_user, {"kind": "workout", "workout_id": workout.id}
            )

    def test_normalizes_week_start_and_explains_weekdays(self) -> None:
        resolved = resolve_view_context(
            self.user, {"kind": "week", "week_start_date": date(2026, 8, 12)}
        )

        self.assertIsInstance(resolved, WeekViewContext)
        assert isinstance(resolved, WeekViewContext)
        self.assertEqual(resolved.week_start_date, date(2026, 8, 10))
        self.assertIn("Tuesday is 2026-08-11", resolved.coach_instruction())
