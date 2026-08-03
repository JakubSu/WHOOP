from __future__ import annotations

from datetime import timedelta
from typing import Any, cast
from unittest.mock import MagicMock

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from whoop.exceptions import WhoopConnectionNotFound, WhoopValidationError
from whoop.models import WhoopSnapshot
from whoop.storage.connection_repository import WhoopConnectionRepository
from whoop.storage.snapshot_repository import WhoopSnapshotRepository
from whoop.storage.token_crypto import TokenCrypto
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
    WhoopToken,
    Workout,
    WorkoutScore,
    ZoneDurations,
)
from whoop.workflows.connection import DisconnectWhoopService
from whoop.workflows.summary import GetWhoopSummaryService, WhoopApiServices


@override_settings(WHOOP_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"))
class WhoopSummaryWorkflowTests(TestCase):
    def setUp(self) -> None:
        User = cast(Any, get_user_model())
        self.user = User.objects.create_user(
            email="summary@example.com", password="password"
        )
        self.user_id = str(self.user.id)
        self.connection_repository = WhoopConnectionRepository(TokenCrypto())
        self.snapshot_repository = WhoopSnapshotRepository()
        self.auth_service = MagicMock()
        self.api_services_factory = MagicMock(return_value=_api_services())
        self.service = GetWhoopSummaryService(
            connection_repository=self.connection_repository,
            snapshot_repository=self.snapshot_repository,
            auth_service=self.auth_service,
            api_services_factory=self.api_services_factory,
        )

    def test_disconnected_user_raises_connection_not_found(self) -> None:
        with self.assertRaises(WhoopConnectionNotFound):
            self.service.execute(self.user_id)

    def test_recent_snapshot_is_returned_without_calling_whoop(self) -> None:
        self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=WhoopToken(
                access_token="access-token",
                expires_at=timezone.now() + timedelta(hours=1),
            ),
        )
        self.snapshot_repository.save_snapshot(
            user_id=self.user_id,
            data={
                "snapshot_date": timezone.localdate(),
                "recovery_score": 72.0,
                "sleep_performance_percent": 88.0,
                "day_strain": 9.4,
                "hrv_rmssd_milli": 43.2,
                "resting_heart_rate": 58.0,
                "sleep_duration_minutes": 431,
                "recent_workout_count": 2,
                "raw_payload": {},
            },
        )

        summary = self.service.execute(self.user_id)

        self.assertEqual(summary["recovery_score"], 72.0)
        self.api_services_factory.assert_not_called()

    def test_snapshot_older_than_one_hour_is_refreshed(self) -> None:
        self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=WhoopToken(
                access_token="access-token",
                expires_at=timezone.now() + timedelta(hours=1),
            ),
        )
        snapshot = self.snapshot_repository.save_snapshot(
            user_id=self.user_id,
            data={
                "snapshot_date": timezone.localdate(),
                "recovery_score": 41.0,
                "sleep_performance_percent": 58.0,
                "day_strain": 12.4,
                "hrv_rmssd_milli": 31.2,
                "resting_heart_rate": 64.0,
                "sleep_duration_minutes": 320,
                "recent_workout_count": 0,
                "raw_payload": {},
            },
        )
        WhoopSnapshot.objects.filter(pk=snapshot.pk).update(
            created_at=timezone.now() - timedelta(hours=2),
        )

        summary = self.service.execute(self.user_id)

        self.api_services_factory.assert_called_once_with("access-token")
        self.assertEqual(summary["recovery_score"], 72.0)

    def test_expired_token_is_refreshed_and_snapshot_is_created(self) -> None:
        self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=WhoopToken(
                access_token="old-token",
                refresh_token="refresh-token",
                expires_at=timezone.now() - timedelta(hours=1),
            ),
        )
        self.auth_service.refresh_token.return_value = WhoopToken(
            access_token="new-token",
            refresh_token="refresh-token",
            expires_at=timezone.now() + timedelta(hours=1),
        )

        summary = self.service.execute(self.user_id)

        self.auth_service.refresh_token.assert_called_once_with("refresh-token")
        self.api_services_factory.assert_called_once_with("new-token")
        self.assertEqual(summary["recovery_score"], 72.0)
        self.assertEqual(summary["recent_workout_count"], 1)
        self.assertEqual(len(summary["recent_workouts"]), 1)
        self.assertEqual(summary["recent_workouts"][0]["sport_name"], "running")

    def test_summary_fetches_workouts_from_last_three_rolling_days(self) -> None:
        self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=WhoopToken(
                access_token="access-token",
                expires_at=timezone.now() + timedelta(hours=1),
            ),
        )
        started_at = timezone.now()

        summary = self.service.execute(self.user_id)

        workout_service = self.api_services_factory.return_value.workout_service
        _, kwargs = workout_service.list_workouts.call_args
        self.assertEqual(kwargs["limit"], 25)
        self.assertLessEqual(
            kwargs["start"], started_at - timedelta(days=3) + timedelta(seconds=1)
        )
        self.assertGreaterEqual(kwargs["end"], started_at)
        self.assertEqual(summary["recent_workouts"][0]["duration_minutes"], 45)
        self.assertEqual(summary["recent_workouts"][0]["strain"], 6.8)

    def test_summary_still_saves_snapshot_when_recent_workout_fetch_is_rejected(
        self,
    ) -> None:
        self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=WhoopToken(
                access_token="access-token",
                expires_at=timezone.now() + timedelta(hours=1),
            ),
        )
        self.api_services_factory.return_value.workout_service.list_workouts.side_effect = WhoopValidationError(
            "WHOOP request failed with status 400."
        )

        summary = self.service.execute(self.user_id)

        self.assertEqual(summary["recovery_score"], 72.0)
        self.assertEqual(summary["recent_workout_count"], 0)
        self.assertEqual(summary["recent_workouts"], [])


@override_settings(WHOOP_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"))
class DisconnectWhoopWorkflowTests(TestCase):
    def test_disconnect_revokes_connection_and_clears_profile_whoop_id(self) -> None:
        User = cast(Any, get_user_model())
        user = User.objects.create_user(
            email="disconnect@example.com",
            password="password",
            whoop_user_id="10129",
        )
        connection_repository = WhoopConnectionRepository(TokenCrypto())
        connection = connection_repository.save_connection(
            user_id=str(user.id),
            whoop_user_id=10129,
            token=WhoopToken(access_token="access-token"),
        )
        auth_service = MagicMock()
        service = DisconnectWhoopService(
            auth_service=auth_service,
            connection_repository=connection_repository,
        )

        disconnected = service.execute(str(user.id))

        self.assertTrue(disconnected)
        auth_service.revoke_user_access.assert_called_once_with("access-token")
        connection.refresh_from_db(from_queryset=None)
        user.refresh_from_db()
        self.assertIsNotNone(connection.revoked_at)
        self.assertEqual(user.whoop_user_id, "")


def _api_services() -> WhoopApiServices:
    cycle_service = MagicMock()
    cycle_service.list_cycles.return_value = PaginatedResponse(
        records=[_cycle()], page=PaginationCursor()
    )
    recovery_service = MagicMock()
    recovery_service.list_recoveries.return_value = PaginatedResponse(
        records=[_recovery()], page=PaginationCursor()
    )
    sleep_service = MagicMock()
    sleep_service.list_sleep.return_value = PaginatedResponse(
        records=[_sleep()], page=PaginationCursor()
    )
    workout_service = MagicMock()
    workout_service.list_workouts.return_value = PaginatedResponse(
        records=[_workout()], page=PaginationCursor()
    )
    return WhoopApiServices(
        cycle_service=cycle_service,
        recovery_service=recovery_service,
        sleep_service=sleep_service,
        workout_service=workout_service,
    )


def _cycle() -> Cycle:
    now = timezone.now()
    return Cycle(
        id=1,
        user_id=10129,
        created_at=now,
        updated_at=now,
        start=now,
        end=now,
        timezone_offset="-05:00",
        score_state="SCORED",
        score=CycleScore(
            strain=9.4, kilojoule=8000.0, average_heart_rate=68, max_heart_rate=141
        ),
    )


def _recovery() -> Recovery:
    now = timezone.now()
    return Recovery(
        cycle_id=1,
        sleep_id="sleep-id",
        user_id=10129,
        created_at=now,
        updated_at=now,
        score_state="SCORED",
        score=RecoveryScore(
            user_calibrating=False,
            recovery_score=72.0,
            resting_heart_rate=58.0,
            hrv_rmssd_milli=43.2,
        ),
    )


def _sleep() -> Sleep:
    now = timezone.now()
    return Sleep(
        id="sleep-id",
        cycle_id=1,
        user_id=10129,
        created_at=now,
        updated_at=now,
        start=now,
        end=now,
        timezone_offset="-05:00",
        nap=False,
        score_state="SCORED",
        score=SleepScore(
            stage_summary=SleepStageSummary(
                total_in_bed_time_milli=30272735,
                total_awake_time_milli=1403507,
                total_no_data_time_milli=0,
                total_light_sleep_time_milli=14905851,
                total_slow_wave_sleep_time_milli=6630370,
                total_rem_sleep_time_milli=5879573,
                sleep_cycle_count=3,
                disturbance_count=12,
            ),
            sleep_needed=SleepNeeded(
                baseline_milli=27395716,
                need_from_sleep_debt_milli=352230,
                need_from_recent_strain_milli=208595,
                need_from_recent_nap_milli=-12312,
            ),
            sleep_performance_percentage=88.0,
        ),
    )


def _workout() -> Workout:
    now = timezone.now()
    return Workout(
        id="workout-id",
        user_id=10129,
        created_at=now,
        updated_at=now,
        start=now - timedelta(minutes=45),
        end=now,
        timezone_offset="-05:00",
        sport_name="running",
        score_state="SCORED",
        score=WorkoutScore(
            strain=6.8,
            average_heart_rate=142,
            max_heart_rate=176,
            kilojoule=1800.0,
            percent_recorded=100.0,
            zone_durations=ZoneDurations(
                zone_zero_milli=1,
                zone_one_milli=2,
                zone_two_milli=3,
                zone_three_milli=4,
                zone_four_milli=5,
                zone_five_milli=6,
            ),
            distance_meter=5000.0,
        ),
    )
