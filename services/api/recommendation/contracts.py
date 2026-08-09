from __future__ import annotations

from datetime import date as Date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecommendationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExerciseReference(RecommendationModel):
    id: UUID
    name: str


class ExercisePrescription(RecommendationModel):
    sets: int = Field(default=0, ge=0)
    reps: int = Field(default=0, ge=0)
    time: int = Field(default=0, ge=0)
    weight: Decimal | None = Field(default=None, ge=0)
    weight_unit: Literal["lb", "kg"] = "lb"
    note: str = ""


class ExerciseChanges(RecommendationModel):
    sets: int | None = Field(default=None, ge=0)
    reps: int | None = Field(default=None, ge=0)
    time: int | None = Field(default=None, ge=0)
    weight: Decimal | None = Field(default=None, ge=0)
    weight_unit: Literal["lb", "kg"] | None = None
    note: str | None = None

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one exercise field must be changed.")
        return self


class WorkoutChanges(RecommendationModel):
    name: str | None = None
    date: Date | None = None
    expected_time: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("At least one workout field must be changed.")
        return self


class AddWorkoutPayload(RecommendationModel):
    temporary_id: UUID
    name: str
    date: Date
    expected_time: int = Field(default=0, ge=0)


class UpdateWorkoutPayload(RecommendationModel):
    workout_id: UUID
    changes: WorkoutChanges


class RemoveWorkoutPayload(RecommendationModel):
    workout_id: UUID


class AddExercisePayload(RecommendationModel):
    temporary_id: UUID
    workout_id: UUID | None = None
    temporary_workout_id: UUID | None = None
    exercise: ExerciseReference
    prescription: ExercisePrescription
    position: int = Field(ge=0)

    @model_validator(mode="after")
    def require_one_workout_reference(self):
        if (
            sum(
                value is not None
                for value in (self.workout_id, self.temporary_workout_id)
            )
            != 1
        ):
            raise ValueError("Exactly one workout reference is required.")
        return self


class UpdateExercisePayload(RecommendationModel):
    workout_exercise_id: UUID
    workout_id: UUID | None = None
    changes: ExerciseChanges | None = None
    position: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_change(self):
        if self.changes is None and self.workout_id is None and self.position is None:
            raise ValueError("At least one exercise or placement change is required.")
        return self


class RemoveExercisePayload(RecommendationModel):
    workout_exercise_id: UUID


class OperationBase(RecommendationModel):
    reason: str


class AddWorkoutOperation(OperationBase):
    operation_type: Literal["add_workout"]
    payload: AddWorkoutPayload


class UpdateWorkoutOperation(OperationBase):
    operation_type: Literal["update_workout"]
    payload: UpdateWorkoutPayload


class RemoveWorkoutOperation(OperationBase):
    operation_type: Literal["remove_workout"]
    payload: RemoveWorkoutPayload


class AddExerciseOperation(OperationBase):
    operation_type: Literal["add_exercise"]
    payload: AddExercisePayload


class UpdateExerciseOperation(OperationBase):
    operation_type: Literal["update_exercise"]
    payload: UpdateExercisePayload


class RemoveExerciseOperation(OperationBase):
    operation_type: Literal["remove_exercise"]
    payload: RemoveExercisePayload


RecommendationOperation = Annotated[
    AddWorkoutOperation
    | UpdateWorkoutOperation
    | RemoveWorkoutOperation
    | AddExerciseOperation
    | UpdateExerciseOperation
    | RemoveExerciseOperation,
    Field(discriminator="operation_type"),
]


class RecommendationDraft(RecommendationModel):
    summary: str
    reason: str
    operations: list[RecommendationOperation] = Field(min_length=1)


class ActiveRecommendation(RecommendationModel):
    """Represents the one pending proposal the coach may replace in a conversation."""

    recommendation_id: UUID
    draft: RecommendationDraft
