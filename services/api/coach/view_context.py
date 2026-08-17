"""Validated, trusted descriptions of the training screen behind a coach turn."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any
from uuid import UUID


class InvalidCoachViewContext(ValueError):
    """Raised when a submitted screen context is malformed or unavailable."""


@dataclass(frozen=True)
class WorkoutViewContext:
    workout_id: UUID

    def as_dict(self) -> dict[str, str]:
        return {"kind": "workout", "workout_id": str(self.workout_id)}

    def coach_instruction(self) -> str:
        return (
            f"The user is viewing verified workout {self.workout_id}. "
            "Interpret 'this workout' as that workout. Before proposing a change, "
            "call get_workout with this exact ID."
        )


@dataclass(frozen=True)
class WeekViewContext:
    week_start_date: date

    def as_dict(self) -> dict[str, str]:
        return {"kind": "week", "week_start_date": self.week_start_date.isoformat()}

    def coach_instruction(self) -> str:
        dates = [self.week_start_date + timedelta(days=index) for index in range(7)]
        labels = ", ".join(
            f"{name} is {value.isoformat()}"
            for name, value in zip(
                (
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ),
                dates,
                strict=True,
            )
        )
        return (
            f"The user is viewing the verified week beginning {self.week_start_date.isoformat()}. "
            f"{labels}. Resolve weekday references inside this week. For an existing "
            "workout, search the relevant date before proposing a change; if multiple "
            "workouts match, ask which one."
        )


CoachViewContext = WorkoutViewContext | WeekViewContext


def resolve_view_context(
    user: Any, submitted: dict[str, Any] | None
) -> CoachViewContext | None:
    """Validate browser context and bind it to data owned by the active user."""

    if submitted is None:
        return None
    kind = submitted.get("kind")
    if kind == "workout":
        from training.models import Workout

        workout_id = submitted.get("workout_id")
        if (
            not isinstance(workout_id, UUID)
            or not Workout.objects.filter(pk=workout_id, user_id=str(user.id)).exists()
        ):
            raise InvalidCoachViewContext("The selected workout is not available.")
        return WorkoutViewContext(workout_id=workout_id)
    if kind == "week":
        week_start_date = submitted.get("week_start_date")
        if not isinstance(week_start_date, date):
            raise InvalidCoachViewContext("The selected week is invalid.")
        return WeekViewContext(
            week_start_date=week_start_date - timedelta(days=week_start_date.weekday())
        )
    raise InvalidCoachViewContext("The selected screen is invalid.")
