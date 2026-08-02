from datetime import date as Date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def remove_json_schema_defaults(schema: dict[str, Any]) -> None:
    schema.pop("default", None)
    for value in schema.values():
        if isinstance(value, dict):
            remove_json_schema_defaults(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_json_schema_defaults(item)


class ExercisePrescription(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    exercise_definition_id: str
    sets: int | None = None
    reps: int | None = None
    weight: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None


class ExercisePrescriptionChanges(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    sets: int | None = None
    reps: int | None = None
    weight: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "ExercisePrescriptionChanges":
        if not self.model_dump(exclude_none=True):
            raise ValueError("update_exercise requires at least one change.")
        return self


class WorkoutDraft(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    name: str
    date: Date
    goal: str | None = None
    notes: str | None = None
    exercises: list[ExercisePrescription] = Field(default_factory=list)


class WorkoutMetadataChanges(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    name: str | None = None
    date: Date | None = None
    goal: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "WorkoutMetadataChanges":
        if not self.model_dump(exclude_none=True):
            raise ValueError("update_workout requires at least one change.")
        return self


class UpdateExerciseChanges(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    sets: int | None = None
    reps: int | None = None
    time: int | None = None
    weight: float | None = None
    weight_unit: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> "UpdateExerciseChanges":
        if not self.model_dump(exclude_none=True):
            raise ValueError("update_exercise requires at least one change.")
        return self


class WorkoutPatchOperation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    op: Literal[
        "add_exercise",
        "remove_exercise",
        "replace_exercise",
        "update_exercise",
        "move_exercise",
        "add_workout",
        "remove_workout",
        "update_workout",
        "revise_workout",
    ]
    workout_exercise_id: str | None = None
    after_workout_exercise_id: str | None = None
    replacement_exercise_id: str | None = None
    exercise_id: str | None = None
    exercise: ExercisePrescription | None = None
    replacement: ExercisePrescription | None = None
    changes: UpdateExerciseChanges | None = None
    prescription_changes: ExercisePrescriptionChanges | None = None
    sets: int | None = None
    reps: int | None = None
    time: int | None = None
    weight: float | None = None
    weight_unit: str | None = None
    note: str | None = None
    training_plan_id: str | None = None
    workout_id: str | None = None
    workout: WorkoutDraft | None = None
    proposed_workout: WorkoutDraft | None = None
    workout_changes: WorkoutMetadataChanges | None = None
    reason: str = ""

    @model_validator(mode="after")
    def require_operation_fields(self) -> "WorkoutPatchOperation":
        if self.op == "add_exercise":
            if self.exercise is None and not self.exercise_id:
                raise ValueError("add_exercise requires exercise.")
        elif self.op == "remove_exercise":
            if not self.workout_exercise_id:
                raise ValueError("remove_exercise requires workout_exercise_id.")
        elif self.op == "replace_exercise":
            if (
                (not self.workout_exercise_id or not self.replacement_exercise_id)
                and self.replacement is None
            ):
                raise ValueError("replace_exercise requires workout_exercise_id and replacement.")
        elif self.op == "update_exercise":
            if not self.workout_exercise_id or (self.changes is None and self.prescription_changes is None):
                raise ValueError("update_exercise requires workout_exercise_id and changes.")
        elif self.op == "move_exercise":
            if not self.workout_exercise_id:
                raise ValueError("move_exercise requires workout_exercise_id.")
        elif self.op == "add_workout":
            if not self.training_plan_id or self.workout is None:
                raise ValueError("add_workout requires training_plan_id and workout.")
        elif self.op == "remove_workout":
            if not self.workout_id:
                raise ValueError("remove_workout requires workout_id.")
        elif self.op == "update_workout":
            if not self.workout_id or self.workout_changes is None:
                raise ValueError("update_workout requires workout_id and changes.")
        elif self.op == "revise_workout" and (
            not self.workout_id or self.proposed_workout is None
        ):
            raise ValueError("revise_workout requires workout_id and proposed_workout.")
        return self


ReplaceExerciseOperation = WorkoutPatchOperation
UpdateExerciseOperation = WorkoutPatchOperation
RemoveExerciseOperation = WorkoutPatchOperation
AddExerciseOperation = WorkoutPatchOperation


class WorkoutPatchDraft(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=remove_json_schema_defaults,
    )

    summary: str
    operation: WorkoutPatchOperation
    reason: str = ""


# Backwards-compatible names while callers move to the draft language.
RecommendationOperationOutput = WorkoutPatchOperation
WorkoutRecommendationResponse = WorkoutPatchDraft
