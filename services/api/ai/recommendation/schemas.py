from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator


def remove_json_schema_defaults(schema: dict[str, Any]) -> None:
    schema.pop("default", None)
    for value in schema.values():
        if isinstance(value, dict):
            remove_json_schema_defaults(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    remove_json_schema_defaults(item)


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
        "replace_exercise",
        "update_exercise",
        "remove_exercise",
        "add_exercise",
    ]
    workout_exercise_id: str | None = None
    replacement_exercise_id: str | None = None
    exercise_id: str | None = None
    changes: UpdateExerciseChanges | None = None
    sets: int | None = None
    reps: int | None = None
    time: int | None = None
    weight: float | None = None
    weight_unit: str | None = None
    note: str | None = None
    reason: str = ""

    @model_validator(mode="after")
    def require_operation_fields(self) -> "WorkoutPatchOperation":
        if self.op == "replace_exercise":
            if not self.workout_exercise_id or not self.replacement_exercise_id:
                raise ValueError(
                    "replace_exercise requires workout_exercise_id and replacement_exercise_id."
                )
        elif self.op == "update_exercise":
            if not self.workout_exercise_id or self.changes is None:
                raise ValueError(
                    "update_exercise requires workout_exercise_id and changes."
                )
        elif self.op == "remove_exercise":
            if not self.workout_exercise_id:
                raise ValueError("remove_exercise requires workout_exercise_id.")
        elif self.op == "add_exercise":
            if not self.exercise_id:
                raise ValueError("add_exercise requires exercise_id.")
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
    operations: list[WorkoutPatchOperation]
    reason: str = ""


# Backwards-compatible names while callers move to the draft language.
RecommendationOperationOutput = WorkoutPatchOperation
WorkoutRecommendationResponse = WorkoutPatchDraft
