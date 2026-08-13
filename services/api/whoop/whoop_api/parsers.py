from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from whoop.exceptions import WhoopParseError
from whoop.whoop_api.dto import (
    Cycle,
    CycleScore,
    PaginatedResponse,
    PaginationCursor,
    Recovery,
    RecoveryScore,
    Sleep,
    SleepNeeded,
    SleepScore,
    SleepStageSummary,
    UserBasicProfile,
    UserBodyMeasurement,
    WhoopToken,
    Workout,
    WorkoutScore,
    ZoneDurations,
)


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WhoopParseError(f"Invalid datetime value: {value}") from exc


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_token_response(
    data: dict[str, Any], *, refresh_token: str | None = None
) -> WhoopToken:
    expires_at = None
    if data.get("expires_in") is not None:
        from datetime import timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=int(data["expires_in"])
        )
    return WhoopToken(
        access_token=str(_require(data, "access_token")),
        refresh_token=data.get("refresh_token", refresh_token),
        expires_at=expires_at,
        token_type=data.get("token_type", "Bearer"),
        scope=data.get("scope"),
    )


def parse_user_basic_profile(data: dict[str, Any]) -> UserBasicProfile:
    return UserBasicProfile(
        user_id=int(_require(data, "user_id")),
        email=str(_require(data, "email")),
        first_name=str(_require(data, "first_name")),
        last_name=str(_require(data, "last_name")),
    )


def parse_user_body_measurement(data: dict[str, Any]) -> UserBodyMeasurement:
    return UserBodyMeasurement(
        height_meter=float(_require(data, "height_meter")),
        weight_kilogram=float(_require(data, "weight_kilogram")),
        max_heart_rate=int(_require(data, "max_heart_rate")),
    )


def parse_cycle(data: dict[str, Any]) -> Cycle:
    score = data.get("score")
    return Cycle(
        id=int(_require(data, "id")),
        user_id=int(_require(data, "user_id")),
        created_at=_required_datetime(data, "created_at"),
        updated_at=_required_datetime(data, "updated_at"),
        start=_required_datetime(data, "start"),
        end=parse_datetime(data.get("end")),
        timezone_offset=str(_require(data, "timezone_offset")),
        score_state=str(_require(data, "score_state")),
        score=parse_cycle_score(score) if isinstance(score, dict) else None,
    )


def parse_cycle_score(data: dict[str, Any]) -> CycleScore:
    return CycleScore(
        strain=float(_require(data, "strain")),
        kilojoule=float(_require(data, "kilojoule")),
        average_heart_rate=int(_require(data, "average_heart_rate")),
        max_heart_rate=int(_require(data, "max_heart_rate")),
    )


def parse_recovery(data: dict[str, Any]) -> Recovery:
    score = data.get("score")
    return Recovery(
        cycle_id=int(_require(data, "cycle_id")),
        sleep_id=str(_require(data, "sleep_id")),
        user_id=int(_require(data, "user_id")),
        created_at=_required_datetime(data, "created_at"),
        updated_at=_required_datetime(data, "updated_at"),
        score_state=str(_require(data, "score_state")),
        score=parse_recovery_score(score) if isinstance(score, dict) else None,
    )


def parse_recovery_score(data: dict[str, Any]) -> RecoveryScore:
    return RecoveryScore(
        user_calibrating=bool(_require(data, "user_calibrating")),
        recovery_score=float(_require(data, "recovery_score")),
        resting_heart_rate=float(_require(data, "resting_heart_rate")),
        hrv_rmssd_milli=float(_require(data, "hrv_rmssd_milli")),
        spo2_percentage=_optional_float(data, "spo2_percentage"),
        skin_temp_celsius=_optional_float(data, "skin_temp_celsius"),
    )


def parse_sleep(data: dict[str, Any]) -> Sleep:
    score = data.get("score")
    return Sleep(
        id=str(_require(data, "id")),
        cycle_id=int(_require(data, "cycle_id")),
        user_id=int(_require(data, "user_id")),
        created_at=_required_datetime(data, "created_at"),
        updated_at=_required_datetime(data, "updated_at"),
        start=_required_datetime(data, "start"),
        end=_required_datetime(data, "end"),
        timezone_offset=str(_require(data, "timezone_offset")),
        nap=bool(_require(data, "nap")),
        score_state=str(_require(data, "score_state")),
        v1_id=_optional_int(data, "v1_id"),
        score=parse_sleep_score(score) if isinstance(score, dict) else None,
    )


def parse_sleep_score(data: dict[str, Any]) -> SleepScore:
    return SleepScore(
        stage_summary=parse_sleep_stage_summary(_require(data, "stage_summary")),
        sleep_needed=parse_sleep_needed(_require(data, "sleep_needed")),
        respiratory_rate=_optional_float(data, "respiratory_rate"),
        sleep_performance_percentage=_optional_float(
            data, "sleep_performance_percentage"
        ),
        sleep_consistency_percentage=_optional_float(
            data, "sleep_consistency_percentage"
        ),
        sleep_efficiency_percentage=_optional_float(
            data, "sleep_efficiency_percentage"
        ),
    )


def parse_sleep_stage_summary(data: dict[str, Any]) -> SleepStageSummary:
    return SleepStageSummary(
        total_in_bed_time_milli=int(_require(data, "total_in_bed_time_milli")),
        total_awake_time_milli=int(_require(data, "total_awake_time_milli")),
        total_no_data_time_milli=int(_require(data, "total_no_data_time_milli")),
        total_light_sleep_time_milli=int(
            _require(data, "total_light_sleep_time_milli")
        ),
        total_slow_wave_sleep_time_milli=int(
            _require(data, "total_slow_wave_sleep_time_milli")
        ),
        total_rem_sleep_time_milli=int(_require(data, "total_rem_sleep_time_milli")),
        sleep_cycle_count=int(_require(data, "sleep_cycle_count")),
        disturbance_count=int(_require(data, "disturbance_count")),
    )


def parse_sleep_needed(data: dict[str, Any]) -> SleepNeeded:
    return SleepNeeded(
        baseline_milli=int(_require(data, "baseline_milli")),
        need_from_sleep_debt_milli=int(_require(data, "need_from_sleep_debt_milli")),
        need_from_recent_strain_milli=int(
            _require(data, "need_from_recent_strain_milli")
        ),
        need_from_recent_nap_milli=int(_require(data, "need_from_recent_nap_milli")),
    )


def parse_workout(data: dict[str, Any]) -> Workout:
    score = data.get("score")
    return Workout(
        id=str(_require(data, "id")),
        user_id=int(_require(data, "user_id")),
        created_at=_required_datetime(data, "created_at"),
        updated_at=_required_datetime(data, "updated_at"),
        start=_required_datetime(data, "start"),
        end=_required_datetime(data, "end"),
        timezone_offset=str(_require(data, "timezone_offset")),
        sport_name=str(_require(data, "sport_name")),
        score_state=str(_require(data, "score_state")),
        v1_id=_optional_int(data, "v1_id"),
        score=parse_workout_score(score) if isinstance(score, dict) else None,
        sport_id=_optional_int(data, "sport_id"),
    )


def parse_workout_score(data: dict[str, Any]) -> WorkoutScore:
    return WorkoutScore(
        strain=float(_require(data, "strain")),
        average_heart_rate=int(_require(data, "average_heart_rate")),
        max_heart_rate=int(_require(data, "max_heart_rate")),
        kilojoule=float(_require(data, "kilojoule")),
        percent_recorded=float(_require(data, "percent_recorded")),
        zone_durations=parse_zone_durations(_require(data, "zone_durations")),
        distance_meter=_optional_float(data, "distance_meter"),
        altitude_gain_meter=_optional_float(data, "altitude_gain_meter"),
        altitude_change_meter=_optional_float(data, "altitude_change_meter"),
    )


def parse_zone_durations(data: dict[str, Any]) -> ZoneDurations:
    return ZoneDurations(
        zone_zero_milli=int(_require(data, "zone_zero_milli")),
        zone_one_milli=int(_require(data, "zone_one_milli")),
        zone_two_milli=int(_require(data, "zone_two_milli")),
        zone_three_milli=int(_require(data, "zone_three_milli")),
        zone_four_milli=int(_require(data, "zone_four_milli")),
        zone_five_milli=int(_require(data, "zone_five_milli")),
    )


def parse_paginated_response(
    data: dict[str, Any],
    item_parser: Callable[[dict[str, Any]], Any],
) -> PaginatedResponse[Any]:
    records = _require(data, "records")
    if not isinstance(records, list):
        raise WhoopParseError("WHOOP paginated response records must be a list.")
    return PaginatedResponse(
        records=[item_parser(record) for record in records],
        page=PaginationCursor(next_token=data.get("next_token")),
    )


def _require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise WhoopParseError(f"Missing required WHOOP field '{key}'.")
    return data[key]


def _required_datetime(data: dict[str, Any], key: str) -> datetime:
    parsed = parse_datetime(str(_require(data, key)))
    if parsed is None:
        raise WhoopParseError(f"Missing required WHOOP datetime field '{key}'.")
    return parsed


def _optional_float(data: dict[str, Any], key: str) -> float | None:
    return float(data[key]) if data.get(key) is not None else None


def _optional_int(data: dict[str, Any], key: str) -> int | None:
    return int(data[key]) if data.get(key) is not None else None
