import uuid

from django.test import SimpleTestCase
from pydantic import ValidationError

from recommendation.contracts import (
    AddExercisePayload,
    ExistingWorkoutRef,
    NewWorkoutRef,
    RecommendationDraft,
    RepetitionPrescription,
    TimedSetsPrescription,
    WorkoutChanges,
)


class RecommendationContractTests(SimpleTestCase):
    def test_add_exercise_accepts_existing_workout_repetition_prescription(
        self,
    ) -> None:
        workout_id = uuid.uuid4()
        exercise_id = uuid.uuid4()

        payload = AddExercisePayload.model_validate(
            {
                "workout": {"kind": "existing", "workout_id": str(workout_id)},
                "exercise_id": str(exercise_id),
                "prescription": {
                    "type": "reps",
                    "sets": 3,
                    "reps": 8,
                    "note": "Controlled tempo",
                },
                "position": 0,
            }
        )

        self.assertIsInstance(payload.workout, ExistingWorkoutRef)
        self.assertIsInstance(payload.prescription, RepetitionPrescription)
        if isinstance(payload.workout, ExistingWorkoutRef):
            self.assertEqual(payload.workout.workout_id, workout_id)
        if isinstance(payload.prescription, RepetitionPrescription):
            self.assertEqual(payload.prescription.type, "reps")

    def test_add_exercise_accepts_new_workout_timed_prescription(self) -> None:
        payload = AddExercisePayload.model_validate(
            {
                "workout": {"kind": "new", "temporary_id": "workout_1"},
                "exercise_id": str(uuid.uuid4()),
                "prescription": {
                    "type": "time",
                    "sets": 2,
                    "seconds": 60,
                    "note": "Easy pace",
                },
                "position": 0,
            }
        )

        self.assertIsInstance(payload.workout, NewWorkoutRef)
        self.assertIsInstance(payload.prescription, TimedSetsPrescription)
        if isinstance(payload.workout, NewWorkoutRef):
            self.assertEqual(payload.workout.temporary_id, "workout_1")
        if isinstance(payload.prescription, TimedSetsPrescription):
            self.assertEqual(payload.prescription.seconds, 60)

    def test_add_exercise_rejects_ambiguous_workout_and_prescription_data(self) -> None:
        with self.assertRaises(ValidationError):
            AddExercisePayload.model_validate(
                {
                    "workout": {
                        "kind": "existing",
                        "workout_id": str(uuid.uuid4()),
                        "temporary_id": "workout_1",
                    },
                    "exercise_id": str(uuid.uuid4()),
                    "prescription": {"type": "time", "sets": 1, "seconds": 30},
                    "position": 0,
                }
            )

        with self.assertRaises(ValidationError):
            AddExercisePayload.model_validate(
                {
                    "workout": {"kind": "new", "temporary_id": "workout_1"},
                    "exercise_id": str(uuid.uuid4()),
                    "prescription": {"type": "reps", "sets": 1, "seconds": 30},
                    "position": 0,
                }
            )

    def test_draft_rejects_a_parent_reason(self) -> None:
        with self.assertRaises(ValidationError):
            RecommendationDraft.model_validate(
                {
                    "summary": "Adjust training",
                    "reason": "This is no longer valid here.",
                    "operations": [],
                }
            )

    def test_workout_changes_reject_explicit_null_but_allows_omitted_fields(self) -> None:
        changes = WorkoutChanges.model_validate({"expected_time": 50})
        self.assertEqual(changes.expected_time, 50)
        self.assertEqual(changes.model_dump(), {"expected_time": 50})

        with self.assertRaises(ValidationError):
            WorkoutChanges.model_validate({"name": None, "expected_time": 50})
