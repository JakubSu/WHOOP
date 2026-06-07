from __future__ import annotations

from datetime import datetime

from whoop.whoop_api.parsers import serialize_datetime


def paginated_params(
    *,
    limit: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    next_token: str | None = None,
) -> dict[str, str | int | None]:
    return {
        "limit": limit,
        "start": serialize_datetime(start),
        "end": serialize_datetime(end),
        "nextToken": next_token,
    }
