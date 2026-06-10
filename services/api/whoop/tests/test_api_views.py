from __future__ import annotations

from unittest.mock import MagicMock, patch
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


class WhoopApiViewTests(TestCase):
    def setUp(self) -> None:
        User = cast(Any, get_user_model())
        self.user = User.objects.create_user(
            email="api@example.com", password="password"
        )
        client = APIClient()
        client.force_authenticate(self.user)
        self.client = client

    @patch("whoop.api.views.services.create_build_connect_url_service")
    def test_connect_url_returns_json_payload(self, factory: MagicMock) -> None:
        service = MagicMock()
        service.execute.return_value = {
            "state": "secure-state",
            "connect_url": "https://api.prod.whoop.com/oauth/oauth2/auth?state=secure-state",
        }
        factory.return_value = service

        response = self.client.get(reverse("whoop-connect-url"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "state": "secure-state",
                "connect_url": "https://api.prod.whoop.com/oauth/oauth2/auth?state=secure-state",
            },
        )
        service.execute.assert_called_once_with(user_id=str(self.user.id))

    @patch("whoop.api.views.services.create_complete_connection_service")
    @override_settings(WHOOP_FRONTEND_SUCCESS_URL="")
    def test_callback_completes_connection(self, factory: MagicMock) -> None:
        service = MagicMock()
        factory.return_value = service

        client = APIClient()
        response = cast(
            Any,
            client.get(
                reverse("whoop-callback"),
                {"code": "code-123", "state": "secure-state"},
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"connected": True})
        service.execute.assert_called_once_with(state="secure-state", code="code-123")

    @patch("whoop.api.views.services.create_complete_connection_service")
    def test_callback_rejects_invalid_state(self, factory: MagicMock) -> None:
        service = MagicMock()
        service.execute.side_effect = ValueError(
            "Invalid or expired WHOOP OAuth state."
        )
        factory.return_value = service

        client = APIClient()
        response = client.get(
            reverse("whoop-callback"),
            {"code": "code-123", "state": "expired-state"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid or expired WHOOP OAuth state."},
        )

    @patch("whoop.api.views.services.create_summary_service")
    def test_summary_returns_json(self, factory: MagicMock) -> None:
        service = MagicMock()
        service.execute.return_value = {
            "connected": True,
            "snapshot_date": "2026-06-07",
            "recovery_score": 72.0,
            "sleep_performance_percent": 88.0,
            "day_strain": 9.4,
            "hrv_rmssd_milli": 43.2,
            "resting_heart_rate": 58.0,
            "sleep_duration_minutes": 431,
            "recent_workout_count": 2,
            "refreshed_at": "2026-06-07T14:30:00Z",
        }
        factory.return_value = service

        response = self.client.get(reverse("whoop-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["connected"])

    @patch("whoop.api.views.services.create_disconnect_service")
    def test_disconnect_marks_connection_revoked(self, factory: MagicMock) -> None:
        service = MagicMock()
        service.execute.return_value = True
        factory.return_value = service

        response = self.client.post(reverse("whoop-disconnect"))

        self.assertEqual(response.status_code, 204)
