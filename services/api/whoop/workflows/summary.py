from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from datetime import timezone as datetime_timezone
from typing import Any

from django.utils import timezone

from whoop.exceptions import WhoopConnectionNotFound, WhoopValidationError
from whoop.models import WhoopSnapshot
from whoop.storage.connection_repository import WhoopConnectionRepository
from whoop.storage.snapshot_repository import WhoopSnapshotRepository
from whoop.whoop_api.auth_service import AuthService
from whoop.whoop_api.cycle_service import CycleService
from whoop.whoop_api.dto import Cycle, Recovery, Sleep, Workout
from whoop.whoop_api.recovery_service import RecoveryService
from whoop.whoop_api.sleep_service import SleepService
from whoop.whoop_api.workout_service import WorkoutService


@dataclass(slots=True)
class WhoopApiServices:
    cycle_service: CycleService
    recovery_service: RecoveryService
    sleep_service: SleepService
    workout_service: WorkoutService


SUMMARY_MAX_AGE = timedelta(hours=1)
RECENT_WORKOUT_WINDOW = timedelta(days=3)
RECENT_WORKOUT_LIMIT = 25


class GetWhoopSummaryService:
    def __init__(
        self,
        *,
        connection_repository: WhoopConnectionRepository,
        snapshot_repository: WhoopSnapshotRepository,
        auth_service: AuthService,
        api_services_factory: Callable[[str], WhoopApiServices],
    ) -> None:
        self.connection_repository = connection_repository
        self.snapshot_repository = snapshot_repository
        self.auth_service = auth_service
        self.api_services_factory = api_services_factory

    def execute(self, user_id: str) -> dict[str, Any]:
        connection = self.connection_repository.get_active_for_user(user_id)
        if connection is None:
            raise WhoopConnectionNotFound("WHOOP is not connected.")

        recent_snapshot = self.snapshot_repository.get_recent_for_user(
            user_id,
            max_age=SUMMARY_MAX_AGE,
        )
        if recent_snapshot is not None:
            return serialize_snapshot(recent_snapshot, connected=True)

        token = self.connection_repository.get_tokens(connection)
        if token.is_expired() and token.refresh_token:
            token = self.auth_service.refresh_token(token.refresh_token)
            self.connection_repository.update_tokens(connection, token)

        services = self.api_services_factory(token.access_token)
        snapshot_data = build_snapshot_data(services)
        snapshot = self.snapshot_repository.save_snapshot(
            user_id=user_id, data=snapshot_data
        )
        return serialize_snapshot(snapshot, connected=True)


def build_snapshot_data(services: WhoopApiServices) -> dict[str, Any]:
    now = timezone.now()
    recent_workout_start = now - RECENT_WORKOUT_WINDOW

    cycles = services.cycle_service.list_cycles(limit=1)
    cycle = cycles.records[0] if cycles.records else None
    recoveries = services.recovery_service.list_recoveries(limit=1)
    recovery = recoveries.records[0] if recoveries.records else None
    sleeps = services.sleep_service.list_sleep(limit=1)
    sleep = sleeps.records[0] if sleeps.records else None
    try:
        workouts = services.workout_service.list_workouts(
            limit=RECENT_WORKOUT_LIMIT,
            start=recent_workout_start,
            end=now,
        )
        workout_records = workouts.records
    except WhoopValidationError:
        workout_records = []
    recent_workouts = [
        _serialize_recent_workout(workout) for workout in workout_records
    ]

    return {
        "snapshot_date": timezone.localdate(now),
        "recovery_score": _recovery_score(recovery),
        "sleep_performance_percent": _sleep_performance(sleep),
        "day_strain": _day_strain(cycle),
        "hrv_rmssd_milli": _hrv(recovery),
        "resting_heart_rate": _resting_heart_rate(recovery),
        "sleep_duration_minutes": _sleep_duration_minutes(sleep),
        "recent_workout_count": len(recent_workouts),
        "raw_payload": {
            "cycle_id": cycle.id if cycle else None,
            "recovery_cycle_id": recovery.cycle_id if recovery else None,
            "sleep_id": sleep.id if sleep else None,
            "workout_ids": [workout.id for workout in workout_records],
            "recent_workouts": recent_workouts,
        },
    }


def serialize_snapshot(snapshot: WhoopSnapshot, *, connected: bool) -> dict[str, Any]:
    return {
        "connected": connected,
        "snapshot_date": snapshot.snapshot_date.isoformat(),
        "recovery_score": _float_or_none(snapshot.recovery_score),
        "sleep_performance_percent": _float_or_none(snapshot.sleep_performance_percent),
        "day_strain": _float_or_none(snapshot.day_strain),
        "hrv_rmssd_milli": _float_or_none(snapshot.hrv_rmssd_milli),
        "resting_heart_rate": _float_or_none(snapshot.resting_heart_rate),
        "sleep_duration_minutes": snapshot.sleep_duration_minutes,
        "recent_workout_count": snapshot.recent_workout_count,
        "recent_workouts": snapshot.raw_payload.get("recent_workouts", []),
        "refreshed_at": snapshot.created_at.astimezone(datetime_timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
    }


def disconnected_summary() -> dict[str, Any]:
    return {"connected": False, "detail": "WHOOP is not connected."}


def _recovery_score(recovery: Recovery | None) -> float | None:
    return recovery.score.recovery_score if recovery and recovery.score else None


def _sleep_performance(sleep: Sleep | None) -> float | None:
    return sleep.score.sleep_performance_percentage if sleep and sleep.score else None


def _day_strain(cycle: Cycle | None) -> float | None:
    return cycle.score.strain if cycle and cycle.score else None


def _hrv(recovery: Recovery | None) -> float | None:
    return recovery.score.hrv_rmssd_milli if recovery and recovery.score else None


def _resting_heart_rate(recovery: Recovery | None) -> float | None:
    return recovery.score.resting_heart_rate if recovery and recovery.score else None


def _sleep_duration_minutes(sleep: Sleep | None) -> int | None:
    if not sleep or not sleep.score:
        return None
    stages = sleep.score.stage_summary
    asleep_milli = (
        stages.total_light_sleep_time_milli
        + stages.total_slow_wave_sleep_time_milli
        + stages.total_rem_sleep_time_milli
    )
    return round(asleep_milli / 1000 / 60)


def _serialize_recent_workout(workout: Workout) -> dict[str, Any]:
    score = workout.score
    return {
        "id": workout.id,
        "sport_name": workout.sport_name,
        "start": workout.start.astimezone(datetime_timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "end": workout.end.astimezone(datetime_timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "duration_minutes": round((workout.end - workout.start).total_seconds() / 60),
        "strain": score.strain if score else None,
        "average_heart_rate": score.average_heart_rate if score else None,
        "max_heart_rate": score.max_heart_rate if score else None,
        "kilojoule": score.kilojoule if score else None,
        "distance_meter": score.distance_meter if score else None,
        "score_state": workout.score_state,
    }


def _float_or_none(value: Any) -> float | None:
    return float(value) if value is not None else None
