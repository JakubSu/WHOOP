from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from whoop.whoop_api.auth_service import AuthService
from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.cycle_service import CycleService
from whoop.whoop_api.recovery_service import RecoveryService
from whoop.whoop_api.sleep_service import SleepService
from whoop.whoop_api.user_service import UserService
from whoop.whoop_api.workout_service import WorkoutService


class WhoopApiServiceTests(SimpleTestCase):
    def test_auth_service_builds_authorization_url(self) -> None:
        auth_service = AuthService(
            client=MagicMock(),
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost/callback",
            scopes="read:profile offline",
        )

        url = auth_service.build_authorization_url(state="state-123")

        self.assertIn("client_id=client-id", url)
        self.assertIn("state=state-123", url)
        self.assertIn("scope=read%3Aprofile+offline", url)

    def test_auth_service_exchanges_code(self) -> None:
        client = MagicMock()
        client.post.return_value = {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600}
        auth_service = AuthService(
            client=client,
            client_id="client-id",
            client_secret="client-secret",
            redirect_uri="http://localhost/callback",
            scopes="read:profile",
        )

        token = auth_service.exchange_code("code-123")

        self.assertEqual(token.access_token, "access")
        self.assertEqual(token.refresh_token, "refresh")

    def test_user_service_calls_profile_endpoint(self) -> None:
        client = MagicMock()
        client.get.return_value = {
            "user_id": 10129,
            "email": "jsmith123@whoop.com",
            "first_name": "John",
            "last_name": "Smith",
        }

        profile = UserService(client).get_basic_profile()

        self.assertEqual(profile.first_name, "John")
        client.get.assert_called_once_with("/v2/user/profile/basic")

    def test_cycle_service_sends_pagination_params(self) -> None:
        client = MagicMock()
        client.get.return_value = {"records": [], "next_token": "next-page"}

        page = CycleService(client).list_cycles(
            limit=10,
            start=datetime(2022, 4, 24, 2, 25, tzinfo=timezone.utc),
            next_token="next-page",
        )

        self.assertEqual(page.next_token, "next-page")
        _, kwargs = client.get.call_args
        self.assertEqual(kwargs["params"]["limit"], 10)
        self.assertEqual(kwargs["params"]["nextToken"], "next-page")

    def test_endpoint_services_use_expected_paths(self) -> None:
        client = MagicMock()
        client.get.side_effect = [
            {
                "cycle_id": 93845,
                "sleep_id": "sleep-id",
                "user_id": 10129,
                "created_at": "2022-04-24T11:25:44.774Z",
                "updated_at": "2022-04-24T14:25:44.774Z",
                "score_state": "SCORED",
            },
            {
                "id": "sleep-id",
                "cycle_id": 93845,
                "user_id": 10129,
                "created_at": "2022-04-24T11:25:44.774Z",
                "updated_at": "2022-04-24T14:25:44.774Z",
                "start": "2022-04-24T02:25:44.774Z",
                "end": "2022-04-24T10:25:44.774Z",
                "timezone_offset": "-05:00",
                "nap": False,
                "score_state": "SCORED",
            },
            {
                "id": "workout-id",
                "user_id": 9012,
                "created_at": "2022-04-24T11:25:44.774Z",
                "updated_at": "2022-04-24T14:25:44.774Z",
                "start": "2022-04-24T02:25:44.774Z",
                "end": "2022-04-24T10:25:44.774Z",
                "timezone_offset": "-05:00",
                "sport_name": "running",
                "score_state": "SCORED",
            },
        ]

        RecoveryService(client).get_recovery_for_cycle(93845)
        SleepService(client).get_sleep("sleep-id")
        WorkoutService(client).get_workout("workout-id")

        self.assertEqual(client.get.call_args_list[0].args[0], "/v2/cycle/93845/recovery")
        self.assertEqual(client.get.call_args_list[1].args[0], "/v2/activity/sleep/sleep-id")
        self.assertEqual(client.get.call_args_list[2].args[0], "/v2/activity/workout/workout-id")
