from dataclasses import dataclass

from training.models import Workout


@dataclass(frozen=True)
class WorkoutLanding:
    workout: Workout
    is_today: bool
    has_workout_today: bool
    message: str | None
