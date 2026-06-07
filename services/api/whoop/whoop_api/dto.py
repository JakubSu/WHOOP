from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class WhoopToken:
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    token_type: str = "Bearer"
    scope: str | None = None

    def is_expired(self, *, leeway_seconds: int = 30) -> bool:
        if self.expires_at is None:
            return False
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at.astimezone(timezone.utc) <= datetime.now(timezone.utc) + timedelta(seconds=leeway_seconds)


@dataclass(slots=True)
class PaginationCursor:
    next_token: str | None = None


@dataclass(slots=True)
class PaginatedResponse(Generic[T]):
    records: list[T]
    page: PaginationCursor

    @property
    def next_token(self) -> str | None:
        return self.page.next_token


@dataclass(slots=True)
class UserBasicProfile:
    user_id: int
    email: str
    first_name: str
    last_name: str


@dataclass(slots=True)
class UserBodyMeasurement:
    height_meter: float
    weight_kilogram: float
    max_heart_rate: int


@dataclass(slots=True)
class CycleScore:
    strain: float
    kilojoule: float
    average_heart_rate: int
    max_heart_rate: int


@dataclass(slots=True)
class Cycle:
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    start: datetime
    end: datetime | None
    timezone_offset: str
    score_state: str
    score: CycleScore | None = None


@dataclass(slots=True)
class RecoveryScore:
    user_calibrating: bool
    recovery_score: float
    resting_heart_rate: float
    hrv_rmssd_milli: float
    spo2_percentage: float | None = None
    skin_temp_celsius: float | None = None


@dataclass(slots=True)
class Recovery:
    cycle_id: int
    sleep_id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    score_state: str
    score: RecoveryScore | None = None


@dataclass(slots=True)
class SleepNeeded:
    baseline_milli: int
    need_from_sleep_debt_milli: int
    need_from_recent_strain_milli: int
    need_from_recent_nap_milli: int


@dataclass(slots=True)
class SleepStageSummary:
    total_in_bed_time_milli: int
    total_awake_time_milli: int
    total_no_data_time_milli: int
    total_light_sleep_time_milli: int
    total_slow_wave_sleep_time_milli: int
    total_rem_sleep_time_milli: int
    sleep_cycle_count: int
    disturbance_count: int


@dataclass(slots=True)
class SleepScore:
    stage_summary: SleepStageSummary
    sleep_needed: SleepNeeded
    respiratory_rate: float | None = None
    sleep_performance_percentage: float | None = None
    sleep_consistency_percentage: float | None = None
    sleep_efficiency_percentage: float | None = None


@dataclass(slots=True)
class Sleep:
    id: str
    cycle_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    start: datetime
    end: datetime
    timezone_offset: str
    nap: bool
    score_state: str
    v1_id: int | None = None
    score: SleepScore | None = None


@dataclass(slots=True)
class ZoneDurations:
    zone_zero_milli: int
    zone_one_milli: int
    zone_two_milli: int
    zone_three_milli: int
    zone_four_milli: int
    zone_five_milli: int


@dataclass(slots=True)
class WorkoutScore:
    strain: float
    average_heart_rate: int
    max_heart_rate: int
    kilojoule: float
    percent_recorded: float
    zone_durations: ZoneDurations
    distance_meter: float | None = None
    altitude_gain_meter: float | None = None
    altitude_change_meter: float | None = None


@dataclass(slots=True)
class Workout:
    id: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    start: datetime
    end: datetime
    timezone_offset: str
    sport_name: str
    score_state: str
    v1_id: int | None = None
    score: WorkoutScore | None = None
    sport_id: int | None = None
