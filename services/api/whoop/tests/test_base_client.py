from __future__ import annotations

from unittest.mock import MagicMock

from django.test import SimpleTestCase

from whoop.exceptions import (
    WhoopError,
    WhoopNotFoundError,
    WhoopRateLimitError,
    WhoopServerError,
    WhoopValidationError,
)
from whoop.whoop_api.base_client import BaseWhoopClient


class FakeResponse:
    def __init__(
        self, status_code: int, payload: dict | None = None, json_error: bool = False
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self) -> dict:
        if self._json_error:
            raise ValueError("invalid json")
        return self._payload or {}


class BaseWhoopClientTests(SimpleTestCase):
    def test_adds_auth_header_when_token_is_available(self) -> None:
        session = MagicMock()
        session.request.return_value = FakeResponse(200, {"ok": True})
        client = BaseWhoopClient(access_token="abc123", session=session)

        client.get("/v2/user/profile/basic")

        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer abc123")
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")

    def test_passes_cleaned_query_params(self) -> None:
        session = MagicMock()
        session.request.return_value = FakeResponse(200, {"records": []})
        client = BaseWhoopClient(access_token="token", session=session)

        client.get("/v2/cycle", params={"limit": 10, "nextToken": "abc", "start": None})

        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["params"], {"limit": 10, "nextToken": "abc"})

    def test_maps_common_http_errors(self) -> None:
        for status_code, error_type in [
            (404, WhoopNotFoundError),
            (429, WhoopRateLimitError),
            (422, WhoopValidationError),
            (500, WhoopServerError),
        ]:
            with self.subTest(status_code=status_code):
                session = MagicMock()
                session.request.return_value = FakeResponse(status_code, {})
                client = BaseWhoopClient(access_token="token", session=session)

                with self.assertRaises(error_type):
                    client.get("/v2/cycle")

    def test_rejects_malformed_json(self) -> None:
        session = MagicMock()
        session.request.return_value = FakeResponse(200, json_error=True)
        client = BaseWhoopClient(access_token="token", session=session)

        with self.assertRaises(WhoopError):
            client.get("/v2/cycle")
