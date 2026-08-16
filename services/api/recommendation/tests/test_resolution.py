from datetime import date
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase

from coach.models import CoachConversation
from recommendation.contracts import RecommendationDraft
from recommendation.models import Recommendation
from recommendation.services import (
    RecommendationConflict,
    accept_recommendation,
    create_recommendation,
    reject_operation,
    reject_recommendation,
)
from training.models import Exercise, Workout, WorkoutExercise


class RecommendationResolutionTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = cast(Any, user_model.objects).create_user(
            email="resolution@example.com", password="strong-password"
        )
        self.conversation = CoachConversation.objects.create(user=self.user)
        self.exercise = Exercise.objects.create(
            name="Interval",
            muscle_group=Exercise.MuscleGroup.QUADS,
            prescription_type=Exercise.PrescriptionType.TIMED,
        )

    def test_accepts_new_workout_and_timed_exercise_via_local_reference(self) -> None:
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Add intervals",
                    "operations": [
                        {
                            "operation_type": "add_exercise",
                            "reason": "Build aerobic capacity.",
                            "payload": {
                                "workout": {
                                    "kind": "new",
                                    "temporary_id": "workout_1",
                                },
                                "exercise_id": str(self.exercise.id),
                                "prescription": {
                                    "type": "time",
                                    "sets": 2,
                                    "seconds": 60,
                                },
                                "position": 0,
                            },
                        },
                        {
                            "operation_type": "add_workout",
                            "reason": "Schedule an interval session.",
                            "payload": {
                                "temporary_id": "workout_1",
                                "name": "Intervals",
                                "date": "2026-08-12",
                            },
                        },
                    ],
                }
            ),
        )

        accept_recommendation(user=self.user, recommendation_id=str(recommendation.id))

        workout_exercise = WorkoutExercise.objects.get(exercise=self.exercise)
        self.assertEqual(workout_exercise.workout.name, "Intervals")
        self.assertEqual(workout_exercise.sets, 2)
        self.assertEqual(workout_exercise.time, 60)

    def test_moves_an_exercise_using_target_workout_id(self) -> None:
        source = Workout.objects.create(
            user_id=str(self.user.id), name="Source", date=date(2026, 8, 12)
        )
        target = Workout.objects.create(
            user_id=str(self.user.id), name="Target", date=date(2026, 8, 13)
        )
        workout_exercise = WorkoutExercise.objects.create(
            workout=source, exercise=self.exercise, sets=1, time=30
        )
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Move interval",
                    "operations": [
                        {
                            "operation_type": "update_exercise",
                            "reason": "Keep intervals with the target session.",
                            "payload": {
                                "workout_exercise_id": str(workout_exercise.id),
                                "target_workout_id": str(target.id),
                            },
                        }
                    ],
                }
            ),
        )

        accept_recommendation(user=self.user, recommendation_id=str(recommendation.id))

        workout_exercise.refresh_from_db()
        self.assertEqual(workout_exercise.workout_id, target.id)

    def test_rejecting_new_workout_rejects_its_child_exercise_operations(self) -> None:
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Add intervals",
                    "operations": [
                        {
                            "operation_type": "add_workout",
                            "reason": "Schedule an interval session.",
                            "payload": {
                                "temporary_id": "workout_1",
                                "name": "Intervals",
                                "date": "2026-08-12",
                            },
                        },
                        {
                            "operation_type": "add_exercise",
                            "reason": "Build aerobic capacity.",
                            "payload": {
                                "workout": {"kind": "new", "temporary_id": "workout_1"},
                                "exercise_id": str(self.exercise.id),
                                "prescription": {
                                    "type": "time",
                                    "sets": 2,
                                    "seconds": 60,
                                },
                                "position": 0,
                            },
                        },
                    ],
                }
            ),
        )
        parent = recommendation.operations.get(operation_type="add_workout")

        reject_operation(
            user=self.user,
            recommendation_id=str(recommendation.id),
            operation_id=str(parent.id),
        )

        self.assertFalse(recommendation.operations.filter(status="pending").exists())
        self.assertEqual(Workout.objects.filter(name="Intervals").count(), 0)

    def test_bulk_resolution_rejects_a_historical_recommendation(self) -> None:
        workout = Workout.objects.create(
            user_id=str(self.user.id), name="Intervals", date=date(2026, 8, 12)
        )
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Rename workout",
                    "operations": [
                        {
                            "operation_type": "update_workout",
                            "reason": "Keep it clear.",
                            "payload": {
                                "workout_id": str(workout.id),
                                "changes": {"name": "Easy intervals"},
                            },
                        }
                    ],
                }
            ),
        )
        recommendation.status = Recommendation.Status.SUPERSEDED
        recommendation.save(update_fields=["status"])

        with self.assertRaisesRegex(RecommendationConflict, "no longer active"):
            accept_recommendation(
                user=self.user, recommendation_id=str(recommendation.id)
            )
        with self.assertRaisesRegex(RecommendationConflict, "no longer active"):
            reject_recommendation(
                user=self.user, recommendation_id=str(recommendation.id)
            )

    def test_accepting_duration_only_workout_update_preserves_required_fields(self) -> None:
        workout = Workout.objects.create(
            user_id=str(self.user.id),
            name="Sprints",
            date=date(2026, 8, 14),
            expected_time=30,
        )
        recommendation = create_recommendation(
            user=self.user,
            conversation=self.conversation,
            draft=RecommendationDraft.model_validate(
                {
                    "summary": "Allow more time for sprints",
                    "operations": [
                        {
                            "operation_type": "update_workout",
                            "reason": "Account for added sprint work.",
                            "payload": {
                                "workout_id": str(workout.id),
                                "changes": {"expected_time": 50},
                            },
                        }
                    ],
                }
            ),
        )
        operation = recommendation.operations.get(operation_type="update_workout")
        self.assertEqual(operation.payload["changes"], {"expected_time": 50})

        accept_recommendation(user=self.user, recommendation_id=str(recommendation.id))

        workout.refresh_from_db()
        self.assertEqual(workout.name, "Sprints")
        self.assertEqual(workout.date, date(2026, 8, 14))
        self.assertEqual(workout.expected_time, 50)
