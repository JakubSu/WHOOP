from __future__ import annotations

from typing import Any

import requests

from whoop.exceptions import (
    WhoopAuthError,
    WhoopError,
    WhoopNotFoundError,
    WhoopRateLimitError,
    WhoopServerError,
    WhoopValidationError,
)


class BaseWhoopClient:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        base_url: str = "https://api.prod.whoop.com/developer",
        session: requests.Session | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.request("POST", path, data=data, params=params)

    def delete(self, path: str, *, params: dict[str, Any] | None = None) -> None:
        self.request("DELETE", path, params=params, expect_json=False)

    def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expect_json: bool = True,
    ) -> dict[str, Any]:
        response = self.session.request(
            method=method,
            url=self._url(path),
            headers=self._headers(),
            data=data,
            params=self._clean_params(params),
            timeout=self.timeout,
        )
        self._raise_for_status(response)

        if not expect_json:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            raise WhoopError("WHOOP API response was not valid JSON.") from exc

        if not isinstance(payload, dict):
            raise WhoopError("WHOOP API response payload was not an object.")
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _clean_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
        if params is None:
            return None
        return {key: value for key, value in params.items() if value is not None}

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        status_code = response.status_code
        if status_code < 400:
            return
        if status_code == 401:
            raise WhoopAuthError("WHOOP authorization failed.")
        if status_code == 404:
            raise WhoopNotFoundError("WHOOP resource was not found.")
        if status_code == 429:
            raise WhoopRateLimitError("WHOOP rate limit exceeded.")
        if 400 <= status_code < 500:
            raise WhoopValidationError(f"WHOOP request failed with status {status_code}.")
        raise WhoopServerError(f"WHOOP server error with status {status_code}.")
