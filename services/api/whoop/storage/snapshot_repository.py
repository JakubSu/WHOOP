from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.utils import timezone

from whoop.models import WhoopSnapshot


class WhoopSnapshotRepository:
    def get_latest_for_user(self, user_id: str) -> WhoopSnapshot | None:
        return WhoopSnapshot.objects.filter(user_id=user_id).order_by("-snapshot_date", "-created_at").first()

    def get_today_for_user(self, user_id: str) -> WhoopSnapshot | None:
        return WhoopSnapshot.objects.filter(user_id=user_id, snapshot_date=timezone.localdate()).order_by("-created_at").first()

    def save_snapshot(self, *, user_id: str, data: dict[str, Any]) -> WhoopSnapshot:
        return WhoopSnapshot.objects.create(
            user_id=user_id,
            snapshot_date=data["snapshot_date"],
            recovery_score=_decimal_or_none(data.get("recovery_score")),
            sleep_performance_percent=_decimal_or_none(data.get("sleep_performance_percent")),
            day_strain=_decimal_or_none(data.get("day_strain")),
            hrv_rmssd_milli=_decimal_or_none(data.get("hrv_rmssd_milli")),
            resting_heart_rate=_decimal_or_none(data.get("resting_heart_rate")),
            sleep_duration_minutes=data.get("sleep_duration_minutes"),
            recent_workout_count=data.get("recent_workout_count", 0),
            raw_payload=data.get("raw_payload", {}),
        )


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
