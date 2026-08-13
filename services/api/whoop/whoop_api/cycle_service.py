from __future__ import annotations

from datetime import datetime

from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.dto import Cycle, PaginatedResponse, Sleep
from whoop.whoop_api.pagination import paginated_params
from whoop.whoop_api.parsers import parse_cycle, parse_paginated_response, parse_sleep


class CycleService:
    def __init__(self, client: BaseWhoopClient) -> None:
        self.client = client

    def get_cycle(self, cycle_id: int) -> Cycle:
        return parse_cycle(self.client.get(f"/v2/cycle/{cycle_id}"))

    def list_cycles(
        self,
        *,
        limit: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        next_token: str | None = None,
    ) -> PaginatedResponse[Cycle]:
        payload = self.client.get(
            "/v2/cycle",
            params=paginated_params(
                limit=limit, start=start, end=end, next_token=next_token
            ),
        )
        return parse_paginated_response(payload, parse_cycle)

    def get_sleep_for_cycle(self, cycle_id: int) -> Sleep:
        return parse_sleep(self.client.get(f"/v2/cycle/{cycle_id}/sleep"))
