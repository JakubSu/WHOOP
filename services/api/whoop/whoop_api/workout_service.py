from __future__ import annotations

from datetime import datetime

from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.dto import PaginatedResponse, Workout
from whoop.whoop_api.pagination import paginated_params
from whoop.whoop_api.parsers import parse_paginated_response, parse_workout


class WorkoutService:
    def __init__(self, client: BaseWhoopClient) -> None:
        self.client = client

    def get_workout(self, workout_id: str | int) -> Workout:
        return parse_workout(self.client.get(f"/v2/activity/workout/{workout_id}"))

    def list_workouts(
        self,
        *,
        limit: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        next_token: str | None = None,
    ) -> PaginatedResponse[Workout]:
        payload = self.client.get(
            "/v2/activity/workout",
            params=paginated_params(limit=limit, start=start, end=end, next_token=next_token),
        )
        return parse_paginated_response(payload, parse_workout)
