from django.test import TestCase

from training import services
from training.models import Exercise, Workout, WorkoutExercise


class WorkoutSnapshotServiceTests(TestCase):
    user_id = "user-1"
    other_user_id = "user-2"

    def test_create_and_read_snapshot_with_ordered_exercises(self) -> None:
        bench = services.create_exercise({"name": "Bench Press"}, user_id=self.user_id)
        row = services.create_exercise({"name": "Row"}, user_id=self.user_id)

        snapshot = services.create_workout_snapshot(
            {
                "name": "Upper Body",
                "workout_type": Workout.Type.STRENGTH,
                "exercises": [
                    {
                        "snapshot_exercise_key": "bench-a",
                        "exercise": str(bench.id),
                        "position": 2,
                        "sets": 4,
                        "reps": 8,
                    },
                    {
                        "snapshot_exercise_key": "row-a",
                        "exercise": str(row.id),
                        "position": 1,
                        "sets": 3,
                        "reps": 12,
                    },
                ],
            },
            user_id=self.user_id,
        )

        self.assertEqual(snapshot.name, "Upper Body")
        self.assertEqual([exercise.position for exercise in snapshot.exercises], [1, 2])
        self.assertEqual(snapshot.exercises[0].exercise.name, "Row")
        self.assertEqual(snapshot.exercises[0].snapshot_exercise_key, snapshot.exercises[0].workout_exercise_id)

    def test_update_workout_fields_without_changing_exercises(self) -> None:
        exercise = services.create_exercise({"name": "Bench Press"}, user_id=self.user_id)
        snapshot = services.create_workout_snapshot(
            {
                "name": "Upper Body",
                "exercises": [
                    {
                        "snapshot_exercise_key": "bench-a",
                        "exercise": str(exercise.id),
                        "position": 1,
                    }
                ],
            },
            user_id=self.user_id,
        )

        updated = services.update_workout_snapshot(
            str(snapshot.id),
            {"name": "Upper Strength"},
            user_id=self.user_id,
        )

        self.assertEqual(updated.name, "Upper Strength")
        self.assertEqual(len(updated.exercises), 1)

    def test_replace_exercises_preserves_referenced_workout_exercise_id(self) -> None:
        bench = services.create_exercise({"name": "Bench Press"}, user_id=self.user_id)
        row = services.create_exercise({"name": "Row"}, user_id=self.user_id)
        snapshot = services.create_workout_snapshot(
            {
                "name": "Upper Body",
                "exercises": [
                    {
                        "snapshot_exercise_key": "bench-a",
                        "exercise": str(bench.id),
                        "position": 1,
                        "reps": 8,
                    }
                ],
            },
            user_id=self.user_id,
        )
        existing_id = snapshot.exercises[0].workout_exercise_id

        updated = services.update_workout_snapshot(
            str(snapshot.id),
            {
                "exercises": [
                    {
                        "workout_exercise_id": existing_id,
                        "snapshot_exercise_key": str(existing_id),
                        "exercise": str(bench.id),
                        "position": 2,
                        "reps": 10,
                    },
                    {
                        "snapshot_exercise_key": "row-a",
                        "exercise": str(row.id),
                        "position": 1,
                    },
                ]
            },
            user_id=self.user_id,
        )

        self.assertEqual(WorkoutExercise.objects.count(), 2)
        self.assertIn(existing_id, [exercise.workout_exercise_id for exercise in updated.exercises])
        self.assertEqual([exercise.position for exercise in updated.exercises], [1, 2])

    def test_rejects_stale_expected_version(self) -> None:
        snapshot = services.create_workout_snapshot({"name": "Upper Body"}, user_id=self.user_id)

        with self.assertRaises(services.StaleWorkoutSnapshotVersion):
            services.update_workout_snapshot(
                str(snapshot.id),
                {"expected_version": "stale-version", "name": "Upper Strength"},
                user_id=self.user_id,
            )

    def test_delete_snapshot_deletes_workout_and_nested_exercises(self) -> None:
        exercise = services.create_exercise({"name": "Bench Press"}, user_id=self.user_id)
        snapshot = services.create_workout_snapshot(
            {
                "name": "Upper Body",
                "exercises": [
                    {
                        "snapshot_exercise_key": "bench-a",
                        "exercise": str(exercise.id),
                        "position": 1,
                    }
                ],
            },
            user_id=self.user_id,
        )

        services.delete_workout_snapshot(str(snapshot.id), user_id=self.user_id)

        self.assertEqual(Workout.objects.count(), 0)
        self.assertEqual(WorkoutExercise.objects.count(), 0)

    def test_rejects_other_users_exercise(self) -> None:
        exercise = services.create_exercise({"name": "Bench Press"}, user_id=self.other_user_id)

        with self.assertRaises(ValueError):
            services.create_workout_snapshot(
                {
                    "name": "Upper Body",
                    "exercises": [
                        {
                            "snapshot_exercise_key": "bench-a",
                            "exercise": str(exercise.id),
                            "position": 1,
                        }
                    ],
                },
                user_id=self.user_id,
            )

    def test_allows_global_exercise(self) -> None:
        exercise = Exercise.objects.create(name="Push-Up", user_id="")

        snapshot = services.create_workout_snapshot(
            {
                "name": "Bodyweight",
                "exercises": [
                    {
                        "snapshot_exercise_key": "push-a",
                        "exercise": str(exercise.id),
                        "position": 1,
                    }
                ],
            },
            user_id=self.user_id,
        )

        self.assertEqual(snapshot.exercises[0].exercise.name, "Push-Up")
