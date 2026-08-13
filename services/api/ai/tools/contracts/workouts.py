"""Safe training workout contracts for AI tools."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkoutSummary(BaseModel):
    """The bounded summary returned when searching user-owned workouts."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    date: date
    expected_time: int


class WorkoutExerciseDetail(BaseModel):
    """The safe exercise details included in a single workout lookup."""

    model_config = ConfigDict(extra="forbid")

    workout_exercise_id: UUID
    exercise_id: UUID
    name: str
    position: int
    sets: int
    reps: int
    time: int
    weight: float | None
    weight_unit: str
    note: str


class WorkoutDetail(WorkoutSummary):
    """A user-owned workout with its ordered exercise prescriptions."""

    exercises: list[WorkoutExerciseDetail]
