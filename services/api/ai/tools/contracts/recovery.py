"""Safe normalized WHOOP summary contract."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class WhoopSummary(BaseModel):
    """The cached health metrics that are safe to expose to a coach tool."""

    model_config = ConfigDict(extra="forbid")

    snapshot_date: date
    recovery_score: float | None
    sleep_performance_percent: float | None
    day_strain: float | None
    hrv_rmssd_milli: float | None
    resting_heart_rate: float | None
    sleep_duration_minutes: int | None
    recent_workout_count: int
    recent_workouts: list[dict[str, object]]
    refreshed_at: datetime
