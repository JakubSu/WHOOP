from __future__ import annotations

from datetime import datetime

from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.dto import PaginatedResponse, Recovery
from whoop.whoop_api.pagination import paginated_params
from whoop.whoop_api.parsers import parse_paginated_response, parse_recovery


class RecoveryService:
    def __init__(self, client: BaseWhoopClient) -> None:
        self.client = client

    def list_recoveries(
        self,
        *,
        limit: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        next_token: str | None = None,
    ) -> PaginatedResponse[Recovery]:
        payload = self.client.get(
            "/v2/recovery",
            params=paginated_params(limit=limit, start=start, end=end, next_token=next_token),
        )
        return parse_paginated_response(payload, parse_recovery)

    def get_recovery_for_cycle(self, cycle_id: int) -> Recovery:
        return parse_recovery(self.client.get(f"/v2/cycle/{cycle_id}/recovery"))
