from __future__ import annotations

from datetime import datetime

from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.dto import PaginatedResponse, Sleep
from whoop.whoop_api.pagination import paginated_params
from whoop.whoop_api.parsers import parse_paginated_response, parse_sleep


class SleepService:
    def __init__(self, client: BaseWhoopClient) -> None:
        self.client = client

    def get_sleep(self, sleep_id: str | int) -> Sleep:
        return parse_sleep(self.client.get(f"/v2/activity/sleep/{sleep_id}"))

    def list_sleep(
        self,
        *,
        limit: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        next_token: str | None = None,
    ) -> PaginatedResponse[Sleep]:
        payload = self.client.get(
            "/v2/activity/sleep",
            params=paginated_params(
                limit=limit, start=start, end=end, next_token=next_token
            ),
        )
        return parse_paginated_response(payload, parse_sleep)
