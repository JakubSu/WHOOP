from __future__ import annotations

from datetime import timedelta
from typing import Any, cast

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils import timezone

from whoop.models import WhoopSnapshot
from whoop.storage.connection_repository import WhoopConnectionRepository
from whoop.storage.oauth_state_repository import WhoopOAuthStateRepository
from whoop.storage.snapshot_repository import WhoopSnapshotRepository
from whoop.storage.token_crypto import TokenCrypto
from whoop.whoop_api.dto import WhoopToken


class TokenCryptoTests(TestCase):
    def test_missing_key_raises_configuration_error(self) -> None:
        with (
            override_settings(WHOOP_TOKEN_ENCRYPTION_KEY=""),
            self.assertRaises(ImproperlyConfigured),
        ):
            TokenCrypto()


@override_settings(WHOOP_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"))
class WhoopStorageTests(TestCase):
    def setUp(self) -> None:
        User = cast(Any, get_user_model())
        self.user = User.objects.create_user(
            email="whoop@example.com", password="password"
        )
        self.user_id = str(self.user.id)
        self.connection_repository = WhoopConnectionRepository(TokenCrypto())
        self.oauth_state_repository = WhoopOAuthStateRepository()
        self.snapshot_repository = WhoopSnapshotRepository()

    def test_connection_repository_encrypts_and_decrypts_tokens(self) -> None:
        token = WhoopToken(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_at=timezone.now() + timedelta(hours=1),
            scope="read:profile",
        )

        connection = self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=token,
        )
        stored_token = self.connection_repository.get_tokens(connection)

        self.assertNotEqual(connection.access_token_encrypted, "access-token")
        self.assertEqual(stored_token.access_token, "access-token")
        self.assertEqual(stored_token.refresh_token, "refresh-token")

    def test_revoked_connection_is_excluded_from_active_lookup(self) -> None:
        connection = self.connection_repository.save_connection(
            user_id=self.user_id,
            whoop_user_id=10129,
            token=WhoopToken(access_token="access-token"),
        )

        self.connection_repository.mark_revoked(connection)

        self.assertIsNone(self.connection_repository.get_active_for_user(self.user_id))

    def test_snapshot_repository_saves_and_reads_today_snapshot(self) -> None:
        snapshot = self.snapshot_repository.save_snapshot(
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
                "raw_payload": {"cycle_id": 1},
            },
        )

        today = self.snapshot_repository.get_today_for_user(self.user_id)

        self.assertEqual(today, snapshot)
        self.assertEqual(WhoopSnapshot.objects.count(), 1)

    def test_oauth_state_repository_stores_frontend_success_url(self) -> None:
        mapping = self.oauth_state_repository.create(
            user_id=self.user_id,
            frontend_success_url="http://localhost:5173/connect-whoop/success",
            ttl_seconds=600,
        )

        consumed = self.oauth_state_repository.consume(state=mapping.state)

        self.assertIsNotNone(consumed)
        if consumed is None:
            self.fail("Expected stored OAuth state to be returned.")
        self.assertEqual(
            consumed.frontend_success_url,
            "http://localhost:5173/connect-whoop/success",
        )
