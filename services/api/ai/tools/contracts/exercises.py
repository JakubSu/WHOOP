"""Safe exercise-library contract for AI tools."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from training.models import Exercise


class ExerciseSummary(BaseModel):
    """The limited metadata used to identify an available exercise."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    prescription_type: str
    muscle_group: Exercise.MuscleGroup
