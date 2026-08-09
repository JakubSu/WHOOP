from __future__ import annotations

import uuid
from datetime import date
from threading import Event
from typing import Any
from unittest.mock import call, patch

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from ai.implementations.scenario import ScenarioCoachRunner, ScenarioRunnerError
from ai.runner import ActivityChanged, CoachRunRequest, RunCompleted, TextDelta
from coach.models import CoachConversation
from recommendation.models import Recommendation, RecommendationOperation
from training.models import Exercise, Workout


class ScenarioCoachRunnerTests(TransactionTestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="scenario@example.com", password="strong-password"
        )
        self.conversation = CoachConversation.objects.create(user=self.user)
        self.runner = ScenarioCoachRunner()
        self.exercise = Exercise.objects.create(
            user_id="", name="Scenario squat", muscle_group="quads", prescription_type="strength"
        )

    def request(self, content: str) -> CoachRunRequest:
        return CoachRunRequest(
            run_id=uuid.uuid4(),
            conversation_id=self.conversation.id,
            user_id=self.user.id,
            content=content,
            ai_message_batches=[],
        )

    def workout(self, name: str = "First workout") -> Workout:
        return Workout.objects.create(user_id=str(self.user.id), name=name, date=date(2026, 8, 8))

    def test_unknown_code_returns_help_without_writes(self) -> None:
        result = self.runner.run(self.request("hello"))
        self.assertIn("/test search-workouts", result.content)
        self.assertEqual(Recommendation.objects.count(), 0)

    def test_search_workouts_reports_earliest_workout_details(self) -> None:
        self.workout("Later workout").date = date(2026, 8, 9)
        Workout.objects.filter(name="Later workout").update(date=date(2026, 8, 9))
        self.workout("Earlier workout")

        result = self.runner.run(self.request("/test search-workouts"))

        self.assertIn("Earlier workout", result.content)
        self.assertIn("0 exercises", result.content)

    @patch("ai.implementations.scenario.get_whoop_summary")
    def test_recovery_reports_available_summary(self, get_summary: Any) -> None:
        get_summary.return_value = type("Summary", (), {"model_dump": lambda self: {"recovery_score": 82}})()

        result = self.runner.run(self.request("/test recovery"))

        self.assertIn("recovery_score", result.content)

    @patch("ai.implementations.scenario.get_whoop_summary", return_value=None)
    def test_recovery_reports_missing_connection(self, get_summary: Any) -> None:
        result = self.runner.run(self.request("/test recovery"))

        self.assertIn("not connected", result.content)
        get_summary.assert_called_once()

    def test_setup_messages_do_not_create_recommendations(self) -> None:
        cases = (
            "/test search-workouts",
            "/test modify-workout",
            "/test retry-create",
            "/test replace-active",
        )

        for code in cases:
            result = self.runner.run(self.request(code))
            self.assertIn("Setup needed", result.content)

        self.assertEqual(Recommendation.objects.count(), 0)

    @patch("ai.implementations.scenario.search_exercises", return_value=[])
    def test_missing_exercise_returns_setup_message_without_creating_a_recommendation(
        self, search: Any
    ) -> None:
        result = self.runner.run(self.request("/test propose-new-workout"))

        self.assertIn("Setup needed", result.content)
        search.assert_called_once()
        self.assertEqual(Recommendation.objects.count(), 0)

    def test_new_workout_proposal_accepts_reversed_operation_order(self) -> None:
        result = self.runner.run(self.request("/test propose-new-workout"))

        recommendation = Recommendation.objects.get(pk=result.recommendation_id)
        self.assertEqual(recommendation.operations.count(), 2)
        self.assertEqual(
            recommendation.operations.order_by("created_at").first().operation_type,
            RecommendationOperation.OperationType.ADD_EXERCISE,
        )

    def test_modify_workout_replaces_an_active_recommendation(self) -> None:
        self.workout()
        original = self.runner.run(self.request("/test modify-workout"))

        replacement = self.runner.run(self.request("/test modify-workout"))

        original_recommendation = Recommendation.objects.get(pk=original.recommendation_id)
        self.assertEqual(original_recommendation.status, Recommendation.Status.SUPERSEDED)
        self.assertEqual(original_recommendation.replaced_by_id, replacement.recommendation_id)

    def test_replace_active_targets_the_second_workout(self) -> None:
        first = self.workout("First workout")
        second = Workout.objects.create(
            user_id=str(self.user.id),
            name="Second workout",
            date=date(2026, 8, 9),
        )
        self.runner.run(self.request("/test modify-workout"))

        result = self.runner.run(self.request("/test replace-active"))

        operation = Recommendation.objects.get(pk=result.recommendation_id).operations.get()
        self.assertEqual(str(operation.payload["workout_id"]), str(second.id))
        self.assertNotEqual(str(operation.payload["workout_id"]), str(first.id))

    def test_replace_active_requires_a_workout_outside_the_active_proposal(self) -> None:
        self.workout()
        original = self.runner.run(self.request("/test modify-workout"))

        result = self.runner.run(self.request("/test replace-active"))

        self.assertIn("Setup needed", result.content)
        self.assertEqual(Recommendation.objects.count(), 1)
        self.assertEqual(Recommendation.objects.get().id, original.recommendation_id)

    def test_retry_create_returns_one_recommendation(self) -> None:
        self.workout()

        result = self.runner.run(self.request("/test retry-create"))

        self.assertEqual(Recommendation.objects.count(), 1)
        self.assertIsNotNone(result.recommendation_id)

    def test_fail_after_create_raises_after_persisting_recommendation(self) -> None:
        request = self.request("/test fail-after-create")

        with self.assertRaises(ScenarioRunnerError):
            self.runner.run(request)

        recommendation = Recommendation.objects.get(run_id=request.run_id)
        self.assertEqual(recommendation.status, Recommendation.Status.ACTIVE)

    def test_stream_emits_live_tool_activities_and_one_terminal_result(self) -> None:
        self.workout()
        entered = Event()
        release = Event()

        def slow_search(context: Any) -> Any:
            entered.set()
            self.assertTrue(release.wait(timeout=1))
            from ai.tools import search_workouts

            return search_workouts(context)

        request = self.request("/test modify-workout")
        with (
            patch("ai.implementations.scenario.search_workouts", side_effect=slow_search),
            patch("ai.implementations.scenario.sleep") as pause,
        ):
            iterator = iter(self.runner.stream(request))
            first = next(iterator)
            self.assertIsInstance(first, ActivityChanged)
            self.assertEqual(first.activity.status, "running")
            self.assertTrue(entered.wait(timeout=1))
            release.set()
            events = [first, *iterator]

        self.assertEqual(pause.call_args_list, [call(0.75), call(0.75), call(0.75)])

        transitions: dict[uuid.UUID, list[str]] = {}
        for event in events:
            if isinstance(event, ActivityChanged):
                transitions.setdefault(event.activity.id, []).append(event.activity.status)
        self.assertTrue(transitions)
        self.assertTrue(all(statuses == ["running", "completed"] for statuses in transitions.values()))
        self.assertTrue(any(isinstance(event, TextDelta) for event in events))
        self.assertEqual(sum(isinstance(event, RunCompleted) for event in events), 1)
        self.assertIsInstance(events[-1], RunCompleted)
