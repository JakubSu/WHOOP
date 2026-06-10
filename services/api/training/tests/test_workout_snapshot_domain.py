from django.test import SimpleTestCase

from training.domain import (
    ExerciseSummary,
    WorkoutSnapshot,
    WorkoutSnapshotDiffer,
    WorkoutSnapshotExercise,
)


class WorkoutSnapshotDomainTests(SimpleTestCase):
    def test_snapshot_round_trips_through_dict(self) -> None:
        snapshot = self._snapshot()

        round_tripped = WorkoutSnapshot.from_dict(snapshot.to_dict())

        self.assertEqual(round_tripped.to_dict(), snapshot.to_dict())

    def test_llm_context_excludes_persistence_fields(self) -> None:
        context = self._snapshot().to_llm_context()

        self.assertEqual(context["workout"]["name"], "Upper Body")
        self.assertEqual(context["exercises"][0]["name"], "Bench Press")
        self.assertEqual(context["exercises"][0]["sets"], 4)
        self.assertNotIn("user_id", context["workout"])
        self.assertNotIn("version", context["workout"])
        self.assertNotIn("created_at", context["workout"])
        self.assertNotIn("workout_exercise_id", context["exercises"][0])

    def test_differ_detects_workout_and_exercise_changes(self) -> None:
        before = self._snapshot(name="Upper Body", sets=4)
        after = self._snapshot(name="Upper Strength", sets=3)

        diff = WorkoutSnapshotDiffer.compare(before, after).to_dict()

        self.assertEqual(
            diff["workout_changes"]["name"],
            {"before": "Upper Body", "after": "Upper Strength"},
        )
        self.assertEqual(
            diff["modified_exercises"][0]["changes"]["sets"],
            {"before": 4, "after": 3},
        )

    def test_differ_matches_by_snapshot_exercise_key_without_persisted_id(self) -> None:
        before = self._snapshot(workout_exercise_id=None, snapshot_exercise_key="draft-a", reps=8)
        after = self._snapshot(workout_exercise_id=None, snapshot_exercise_key="draft-a", reps=10)

        diff = WorkoutSnapshotDiffer.compare(before, after).to_dict()

        self.assertEqual(diff["added_exercises"], [])
        self.assertEqual(diff["removed_exercises"], [])
        self.assertEqual(
            diff["modified_exercises"][0]["identity"],
            {"type": "snapshot_exercise_key", "value": "draft-a"},
        )
        self.assertEqual(
            diff["modified_exercises"][0]["changes"]["reps"],
            {"before": 8, "after": 10},
        )

    def test_differ_supports_duplicate_exercises(self) -> None:
        before = self._snapshot_with_duplicate_exercises(reps=(8, 10), positions=(1, 2))
        after = self._snapshot_with_duplicate_exercises(reps=(8, 12), positions=(1, 2))

        diff = WorkoutSnapshotDiffer.compare(before, after).to_dict()

        self.assertEqual(len(diff["modified_exercises"]), 1)
        self.assertEqual(diff["modified_exercises"][0]["snapshot_exercise_key"], "bench-b")
        self.assertEqual(
            diff["modified_exercises"][0]["changes"]["reps"],
            {"before": 10, "after": 12},
        )

    def test_differ_handles_reordered_duplicate_exercises(self) -> None:
        before = self._snapshot_with_duplicate_exercises(reps=(8, 10), positions=(1, 2))
        after = self._snapshot_with_duplicate_exercises(reps=(8, 10), positions=(2, 1))

        diff = WorkoutSnapshotDiffer.compare(before, after).to_dict()

        self.assertEqual(len(diff["reordered_exercises"]), 2)
        self.assertEqual(
            {item["snapshot_exercise_key"] for item in diff["reordered_exercises"]},
            {"bench-a", "bench-b"},
        )

    def test_differ_detects_added_and_removed_exercises(self) -> None:
        before = self._snapshot_with_duplicate_exercises(reps=(8,), positions=(1,))
        after = self._snapshot_with_duplicate_exercises(reps=(8, 10), positions=(1, 2))

        diff = WorkoutSnapshotDiffer.compare(before, after).to_dict()

        self.assertEqual(len(diff["added_exercises"]), 1)
        self.assertEqual(diff["added_exercises"][0]["snapshot_exercise_key"], "bench-b")
        self.assertEqual(diff["removed_exercises"], [])

    def _snapshot(
        self,
        *,
        name: str = "Upper Body",
        workout_exercise_id: str | None = "we-1",
        snapshot_exercise_key: str = "we-1",
        sets: int = 4,
        reps: int = 8,
    ) -> WorkoutSnapshot:
        return WorkoutSnapshot(
            id="workout-1",
            user_id="user-1",
            version="opaque-version",
            training_plan=None,
            scheduled_date="2026-06-07",
            name=name,
            workout_type="strength",
            status="planned",
            planned_intensity="moderate",
            planned_duration_minutes=60,
            actual_strain="0.00",
            notes="",
            exercises=[
                WorkoutSnapshotExercise(
                    workout_exercise_id=workout_exercise_id,
                    snapshot_exercise_key=snapshot_exercise_key,
                    exercise=self._exercise(),
                    position=1,
                    sets=sets,
                    reps=reps,
                    load="80.00",
                    intensity="moderate",
                    rest_seconds=120,
                )
            ],
            created_at="2026-06-07T12:00:00Z",
            updated_at="2026-06-07T12:00:00Z",
        )

    def _snapshot_with_duplicate_exercises(
        self,
        *,
        reps: tuple[int, ...],
        positions: tuple[int, ...],
    ) -> WorkoutSnapshot:
        exercises = []
        for index, rep_count in enumerate(reps):
            suffix = chr(ord("a") + index)
            exercises.append(
                WorkoutSnapshotExercise(
                    workout_exercise_id=None,
                    snapshot_exercise_key=f"bench-{suffix}",
                    exercise=self._exercise(),
                    position=positions[index],
                    sets=4,
                    reps=rep_count,
                    load="80.00",
                    intensity="moderate",
                    rest_seconds=120,
                )
            )
        return WorkoutSnapshot(
            id="workout-1",
            user_id="user-1",
            version="opaque-version",
            training_plan=None,
            scheduled_date="2026-06-07",
            name="Upper Body",
            workout_type="strength",
            status="planned",
            exercises=exercises,
        )

    def _exercise(self) -> ExerciseSummary:
        return ExerciseSummary(
            id="exercise-bench",
            name="Bench Press",
            category="strength",
            primary_muscle_group="chest",
            secondary_muscle_groups=["triceps"],
            equipment="barbell",
            default_intensity="moderate",
        )
