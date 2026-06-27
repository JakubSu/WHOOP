from typing import Any

from django.test import TestCase

from ai.recommendation.schemas import WorkoutPatchDraft
from recommendation import services
from recommendation.models import Recommendation, RecommendationOperation
from training import services as training_services
from training.models import Exercise, Workout, WorkoutExercise


class FakeWorkoutPatchGenerator:
    def __init__(self, draft: WorkoutPatchDraft) -> None:
        self.draft = draft
        self.calls: list[dict[str, Any]] = []

    def generate(self, context: dict[str, Any]) -> WorkoutPatchDraft:
        self.calls.append({"context": context})
        return self.draft


class WorkoutRecommendationServiceTests(TestCase):
    user_id = "user-1"
    other_user_id = "user-2"

    def setUp(self) -> None:
        self.bench = Exercise.objects.create(name="Bench Press", user_id=self.user_id)
        self.goblet = Exercise.objects.create(name="Goblet Squat", user_id="")
        self.row = Exercise.objects.create(name="Row", user_id=self.user_id)
        self.workout = Workout.objects.create(name="Upper Body", user_id=self.user_id)
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
        self.row_row_id = str(self.row_row.id)

    def test_context_contains_workout_rows_and_available_exercises(self) -> None:
        context = services.build_workout_recommendation_context(
            self.user_id,
            str(self.workout.id),
        )

        self.assertEqual(context["current_workout"]["id"], str(self.workout.id))
        self.assertEqual(
            context["current_workout"]["exercises"][0]["workout_exercise_id"],
            self.bench_row_id,
        )
        self.assertIn(str(self.goblet.id), [exercise["id"] for exercise in context["available_exercises"]])

    def test_generate_stores_ordered_operations_from_mocked_provider(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Reduce fatigue.",
                "reason": "Recovery is low.",
                "operations": [
                    {
                        "op": "update_exercise",
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3},
                    },
                    {
                        "op": "replace_exercise",
                        "workout_exercise_id": self.row_row_id,
                        "replacement_exercise_id": str(self.goblet.id),
                    },
                ],
            }
        )
        generator = FakeWorkoutPatchGenerator(draft)

        recommendation = services.generate_recommendation_for_workout(
            self.user_id,
            str(self.workout.id),
            generator=generator,
        )

        self.assertEqual(recommendation.summary, "Reduce fatigue.")
        self.assertEqual(recommendation.operations.count(), 2)
        self.assertEqual(generator.calls[0]["context"]["current_workout"]["id"], str(self.workout.id))
        self.assertEqual(
            list(recommendation.operations.values_list("operation_type", flat=True)),
            ["update_exercise", "replace_exercise"],
        )

    def test_generate_rejects_other_users_workout_exercise(self) -> None:
        other_workout = Workout.objects.create(name="Other", user_id=self.other_user_id)
        other_workout_exercise = WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=self.goblet,
        )
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Invalid.",
                "operations": [
                    {
                        "op": "remove_exercise",
                        "workout_exercise_id": str(other_workout_exercise.id),
                    }
                ],
            }
        )

        with self.assertRaises(services.RecommendationValidationError):
            services.generate_recommendation_for_workout(
                self.user_id,
                str(self.workout.id),
                generator=FakeWorkoutPatchGenerator(draft),
            )

    def test_generate_ignores_noop_time_change_for_strength_exercise(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Reduce fatigue.",
                "operations": [
                    {
                        "op": "update_exercise",
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3, "reps": 6, "time": 0},
                    }
                ],
            }
        )

        recommendation = services.generate_recommendation_for_workout(
            self.user_id,
            str(self.workout.id),
            generator=FakeWorkoutPatchGenerator(draft),
        )

        operation = recommendation.operations.get()
        self.assertEqual(operation.payload_json["changes"], {"sets": 3, "reps": 6})

    def test_generate_rejects_positive_time_change_for_strength_exercise(self) -> None:
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Invalid.",
                "operations": [
                    {
                        "op": "update_exercise",
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"time": 30},
                    }
                ],
            }
        )

        with self.assertRaises(services.RecommendationValidationError):
            services.generate_recommendation_for_workout(
                self.user_id,
                str(self.workout.id),
                generator=FakeWorkoutPatchGenerator(draft),
            )

    def test_recommendation_service_does_not_import_ai_infrastructure_plumbing(self) -> None:
        import recommendation.services.workout_recommendation as module

        self.assertFalse(hasattr(module, "get_llm_provider"))
        self.assertFalse(hasattr(module, "FileSystemPromptLoader"))

    def test_approve_replace_exercise_changes_only_workout_exercise_catalog_link(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "replace_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "replacement_exercise_id": str(self.goblet.id),
                    },
                }
            ]
        )

        operation = recommendation.operations.get()
        accepted = services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operation.id),
        )

        workout_exercise = WorkoutExercise.objects.get(pk=self.bench_row_id)
        self.assertEqual(workout_exercise.exercise_id, self.goblet.id)
        self.assertEqual(accepted.status, Recommendation.Status.ACCEPTED)
        operation.refresh_from_db()
        self.assertEqual(operation.status, RecommendationOperation.Status.ACCEPTED)
        self.assertTrue(Exercise.objects.filter(pk=self.bench.id).exists())

    def test_approve_update_exercise_changes_only_workout_specific_fields(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3, "reps": 8},
                    },
                }
            ]
        )

        operation = recommendation.operations.get()
        services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operation.id),
        )

        workout_exercise = WorkoutExercise.objects.get(pk=self.bench_row_id)
        self.assertEqual(workout_exercise.sets, 3)
        self.assertEqual(workout_exercise.reps, 8)
        self.bench.refresh_from_db()
        self.assertEqual(self.bench.name, "Bench Press")

    def test_approve_remove_exercise_deletes_target(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "remove_exercise",
                    "payload_json": {"workout_exercise_id": self.bench_row_id},
                }
            ]
        )

        operation = recommendation.operations.get()
        services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operation.id),
        )

        self.assertFalse(WorkoutExercise.objects.filter(pk=self.bench_row_id).exists())
        self.assertTrue(WorkoutExercise.objects.filter(pk=self.row_row_id).exists())

    def test_approve_add_exercise_creates_workout_exercise(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "add_exercise",
                    "payload_json": {
                        "exercise_id": str(self.goblet.id),
                        "sets": 2,
                        "reps": 10,
                        "weight": 55,
                        "weight_unit": "lb",
                        "note": "Add as finisher.",
                    },
                }
            ]
        )

        operation = recommendation.operations.get()
        services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operation.id),
        )

        added = WorkoutExercise.objects.get(workout=self.workout, exercise=self.goblet)
        self.assertEqual(added.sets, 2)
        self.assertEqual(added.reps, 10)
        self.assertEqual(added.weight, 55)
        self.assertEqual(added.weight_unit, "lb")
        self.assertEqual(added.note, "Add as finisher.")

    def test_accepting_one_operation_leaves_sibling_pending_and_parent_pending(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3},
                    },
                },
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.row_row_id,
                        "changes": {"reps": 10},
                    },
                },
            ]
        )
        first_operation = recommendation.operations.order_by("sequence").first()
        if first_operation is None:
            self.fail("Expected recommendation to have at least one operation.")

        updated = services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(first_operation.id),
        )

        statuses = list(updated.operations.order_by("sequence").values_list("status", flat=True))
        self.assertEqual(statuses, ["accepted", "pending"])
        self.assertEqual(updated.status, Recommendation.Status.PENDING)
        self.assertEqual(WorkoutExercise.objects.get(pk=self.bench_row_id).sets, 3)
        self.assertEqual(WorkoutExercise.objects.get(pk=self.row_row_id).reps, 8)

    def test_accepting_multiple_operations_from_same_recommendation_uses_latest_workout_version(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3},
                    },
                },
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.row_row_id,
                        "changes": {"reps": 10},
                    },
                },
            ]
        )
        operations = list(recommendation.operations.order_by("sequence"))

        services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operations[0].id),
        )
        updated = services.approve_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operations[1].id),
        )

        self.assertEqual(updated.status, Recommendation.Status.ACCEPTED)
        statuses = list(updated.operations.order_by("sequence").values_list("status", flat=True))
        self.assertEqual(statuses, ["accepted", "accepted"])
        self.assertEqual(WorkoutExercise.objects.get(pk=self.bench_row_id).sets, 3)
        self.assertEqual(WorkoutExercise.objects.get(pk=self.row_row_id).reps, 10)

    def test_mixed_operation_decisions_roll_up_to_partial(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3},
                    },
                },
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.row_row_id,
                        "changes": {"reps": 10},
                    },
                },
            ]
        )
        operations = list(recommendation.operations.order_by("sequence"))

        services.approve_recommendation_operation(self.user_id, str(recommendation.id), str(operations[0].id))
        updated = services.reject_recommendation_operation(self.user_id, str(recommendation.id), str(operations[1].id))

        self.assertEqual(updated.status, Recommendation.Status.PARTIAL)

    def test_approval_rejects_stale_workout_version(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3},
                    },
                }
            ]
        )
        training_services.update_workout(self.workout, {"name": "Updated"}, user_id=self.user_id)
        operation = recommendation.operations.get()

        with self.assertRaises(services.RecommendationConflict):
            services.approve_recommendation_operation(
                self.user_id,
                str(recommendation.id),
                str(operation.id),
            )

        operation.refresh_from_db()
        self.assertEqual(operation.status, RecommendationOperation.Status.STALE)

    def test_reject_marks_pending_operation_rejected(self) -> None:
        recommendation = self._create_recommendation(
            [
                {
                    "operation_type": "update_exercise",
                    "payload_json": {
                        "workout_exercise_id": self.bench_row_id,
                        "changes": {"sets": 3},
                    },
                }
            ]
        )
        operation = recommendation.operations.get()

        rejected = services.reject_recommendation_operation(
            self.user_id,
            str(recommendation.id),
            str(operation.id),
        )

        self.assertEqual(rejected.status, Recommendation.Status.REJECTED)
        operation.refresh_from_db()
        self.assertEqual(operation.status, RecommendationOperation.Status.REJECTED)
        self.assertEqual(WorkoutExercise.objects.get(pk=self.bench_row_id).sets, 5)

    def test_other_user_cannot_access_recommendation(self) -> None:
        recommendation = self._create_recommendation([])

        self.assertIsNone(services.get_recommendation(self.other_user_id, str(recommendation.id)))
        with self.assertRaises(services.RecommendationNotFound):
            services.reject_recommendation_operation(
                self.other_user_id,
                str(recommendation.id),
                "00000000-0000-0000-0000-000000000000",
            )

    def _create_recommendation(self, operations: list[dict[str, Any]]) -> Recommendation:
        recommendation = Recommendation.objects.create(
            user_id=self.user_id,
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Test recommendation",
        )
        for index, operation in enumerate(operations, start=1):
            RecommendationOperation.objects.create(
                recommendation=recommendation,
                sequence=index,
                operation_type=operation["operation_type"],
                payload_json=operation["payload_json"],
            )
        return recommendation
