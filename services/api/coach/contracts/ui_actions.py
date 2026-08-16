"""Typed contracts for durable, user-facing coach actions."""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


class ExerciseDraft(BaseModel):
    """AI-provided defaults for creating one library exercise."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    prescription_type: Literal["strength", "timed"]
    muscle_group: Literal[
        "chest",
        "back",
        "shoulders",
        "biceps",
        "triceps",
        "forearms",
        "quads",
        "hamstrings",
        "glutes",
        "calves",
        "core",
        "full_body",
        "other",
    ]
    default_sets: int = Field(default=0, ge=0)
    default_reps: int = Field(default=0, ge=0)
    default_time: int = Field(default=0, ge=0)
    notes: str = ""


class ExerciseResolutionPayload(BaseModel):
    """The data required to render an exercise-resolution choice."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    requested_name: str = Field(min_length=1, max_length=200)
    draft_exercise: ExerciseDraft


class ExerciseResolutionUiActionDraft(BaseModel):
    """A request to create or choose an unavailable exercise."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["exercise_resolution"]
    payload: ExerciseResolutionPayload


# Add future action variants here as a discriminated union when they are introduced.
UiActionDraft: TypeAlias = ExerciseResolutionUiActionDraft
