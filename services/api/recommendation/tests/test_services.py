from typing import Any

from ai.recommendation.schemas import WorkoutPatchDraft
from django.test import TestCase
from training import services as training_services
from training.models import Exercise, TrainingPlan, Workout, WorkoutExercise

from recommendation import services
from recommendation.models import Recommendation


class WorkoutRecommendationServiceTests(TestCase):
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
        self.row_row_id = str(self.row_row.id)

    def test_recommendation_service_does_not_import_ai_infrastructure_plumbing(self) -> None:
        import recommendation.services.recommendation as module

        self.assertFalse(hasattr(module, "get_llm_provider"))
        self.assertFalse(hasattr(module, "FileSystemPromptLoader"))

    def test_accept_replace_exercise_changes_catalog_link(self) -> None:
        recommendation = self._create_recommendation(
            "replace_exercise",
            {
                "workout_exercise_id": self.bench_row_id,
                "replacement_exercise_id": str(self.goblet.id),
            },
        )

        applied = services.accept_recommendation(self.user_id, str(recommendation.id))

        workout_exercise = WorkoutExercise.objects.get(pk=self.bench_row_id)
        self.assertEqual(workout_exercise.exercise_id, self.goblet.id)
        self.assertEqual(applied.status, Recommendation.Status.APPLIED)
        self.assertTrue(Exercise.objects.filter(pk=self.bench.id).exists())

    def test_accept_update_exercise_changes_only_workout_specific_fields(self) -> None:
        recommendation = self._create_recommendation(
            "update_exercise",
            {
                "workout_exercise_id": self.bench_row_id,
                "changes": {"sets": 3, "reps": 8},
            },
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        workout_exercise = WorkoutExercise.objects.get(pk=self.bench_row_id)
        self.assertEqual(workout_exercise.sets, 3)
        self.assertEqual(workout_exercise.reps, 8)
        self.bench.refresh_from_db()
        self.assertEqual(self.bench.name, "Bench Press")

    def test_accept_remove_exercise_deletes_target(self) -> None:
        recommendation = self._create_recommendation(
            "remove_exercise",
            {"workout_exercise_id": self.bench_row_id},
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        self.assertFalse(WorkoutExercise.objects.filter(pk=self.bench_row_id).exists())
        self.assertTrue(WorkoutExercise.objects.filter(pk=self.row_row_id).exists())

    def test_accept_add_exercise_creates_workout_exercise(self) -> None:
        recommendation = self._create_recommendation(
            "add_exercise",
            {
                "exercise": {
                    "exercise_definition_id": str(self.goblet.id),
                    "sets": 2,
                    "reps": 10,
                    "weight": 55,
                    "notes": "Add as finisher.",
                },
            },
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        added = WorkoutExercise.objects.get(workout=self.workout, exercise=self.goblet)
        self.assertEqual(added.sets, 2)
        self.assertEqual(added.reps, 10)
        self.assertEqual(added.weight, 55)
        self.assertEqual(added.note, "Add as finisher.")

    def test_accept_move_exercise_reorders_workout_entries(self) -> None:
        self.bench_row.sort_order = 1
        self.bench_row.save(update_fields=["sort_order"])
        self.row_row.sort_order = 2
        self.row_row.save(update_fields=["sort_order"])
        recommendation = self._create_recommendation(
            "move_exercise",
            {
                "workout_exercise_id": self.bench_row_id,
                "after_workout_exercise_id": self.row_row_id,
            },
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        ordered_ids = list(
            WorkoutExercise.objects.filter(workout=self.workout)
            .order_by("sort_order")
            .values_list("id", flat=True)
        )
        self.assertEqual([str(value) for value in ordered_ids], [self.row_row_id, self.bench_row_id])

    def test_accept_update_workout_changes_metadata_only(self) -> None:
        recommendation = self._create_recommendation(
            "update_workout",
            {
                "workout_id": str(self.workout.id),
                "workout_changes": {"name": "Upper Body Easy", "goal": "ignored"},
            },
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        self.workout.refresh_from_db()
        self.assertEqual(self.workout.name, "Upper Body Easy")
        self.assertEqual(WorkoutExercise.objects.filter(workout=self.workout).count(), 2)

    def test_accept_revise_workout_replaces_workout_entries(self) -> None:
        recommendation = self._create_recommendation(
            "revise_workout",
            {
                "workout_id": str(self.workout.id),
                "proposed_workout": {
                    "name": "Revised Lift",
                    "date": "2026-06-10",
                    "exercises": [
                        {
                            "exercise_definition_id": str(self.goblet.id),
                            "sets": 2,
                            "reps": 10,
                        }
                    ],
                },
            },
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        self.workout.refresh_from_db()
        self.assertEqual(self.workout.name, "Revised Lift")
        self.assertEqual(self.workout.workout_exercises.count(), 1)
        self.assertEqual(self.workout.workout_exercises.get().exercise_id, self.goblet.id)

    def test_accept_add_workout_creates_workout_with_initial_exercises(self) -> None:
        plan = TrainingPlan.objects.create(name="Plan", user_id=self.user_id)
        recommendation = self._create_recommendation(
            "add_workout",
            {
                "training_plan_id": str(plan.id),
                "workout": {
                    "name": "New Lift",
                    "date": "2026-06-10",
                    "exercises": [
                        {
                            "exercise_definition_id": str(self.goblet.id),
                            "sets": 2,
                            "reps": 10,
                        }
                    ],
                },
            },
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        workout = Workout.objects.get(name="New Lift", plan=plan)
        self.assertEqual(workout.workout_exercises.count(), 1)

    def test_accept_remove_workout_deletes_workout(self) -> None:
        recommendation = self._create_recommendation(
            "remove_workout",
            {"workout_id": str(self.workout.id)},
        )

        services.accept_recommendation(self.user_id, str(recommendation.id))

        self.assertFalse(Workout.objects.filter(pk=self.workout.id).exists())

    def test_approval_rejects_stale_workout_version(self) -> None:
        recommendation = self._create_recommendation(
            "update_exercise",
            {
                "workout_exercise_id": self.bench_row_id,
                "changes": {"sets": 3},
            },
        )
        training_services.update_workout(self.workout, {"name": "Updated"}, user_id=self.user_id)

        with self.assertRaises(services.RecommendationConflict):
            services.accept_recommendation(self.user_id, str(recommendation.id))

        recommendation.refresh_from_db()
        self.assertEqual(recommendation.status, Recommendation.Status.STALE)

    def test_reject_marks_pending_recommendation_rejected(self) -> None:
        recommendation = self._create_recommendation(
            "update_exercise",
            {
                "workout_exercise_id": self.bench_row_id,
                "changes": {"sets": 3},
            },
        )

        rejected = services.reject_recommendation(self.user_id, str(recommendation.id))

        self.assertEqual(rejected.status, Recommendation.Status.REJECTED)
        self.assertEqual(WorkoutExercise.objects.get(pk=self.bench_row_id).sets, 5)

    def test_other_user_cannot_access_recommendation(self) -> None:
        recommendation = self._create_recommendation("remove_exercise", {"workout_exercise_id": self.bench_row_id})

        self.assertIsNone(services.get_recommendation(self.other_user_id, str(recommendation.id)))
        with self.assertRaises(services.RecommendationNotFound):
            services.reject_recommendation(self.other_user_id, str(recommendation.id))

    def test_revise_workout_cannot_coexist_with_exercise_recommendation(self) -> None:
        self._create_recommendation("update_exercise", {"workout_exercise_id": self.bench_row_id, "changes": {"sets": 3}})
        draft = WorkoutPatchDraft.model_validate(
            {
                "summary": "Revise workout.",
                "operation": {
                    "op": "revise_workout",
                    "workout_id": str(self.workout.id),
                    "proposed_workout": {
                        "name": "Revised",
                        "date": "2026-06-10",
                        "exercises": [],
                    },
                },
            }
        )

        with self.assertRaises(services.RecommendationValidationError):
            services.create_recommendation_from_workout_patch(
                user_id=self.user_id,
                workout_id=str(self.workout.id),
                draft=draft,
            )

    def _create_recommendation(self, operation_type: str, payload: dict[str, Any]) -> Recommendation:
        return Recommendation.objects.create(
            user_id=self.user_id,
            workout_id=str(self.workout.id),
            snapshot_version=self.workout.updated_at.isoformat(),
            summary="Test recommendation",
            operation_type=operation_type,
            payload_json=payload,
        )
