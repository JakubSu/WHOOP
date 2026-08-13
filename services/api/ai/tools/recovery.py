"""Normalized WHOOP recovery tool."""

from __future__ import annotations

from ai.tools.context import CoachToolContext
from ai.tools.contracts import WhoopSummary
from whoop import services
from whoop.exceptions import WhoopConnectionNotFound


def get_whoop_summary(context: CoachToolContext) -> WhoopSummary | None:
    """Returns the current normalized WHOOP summary for the authenticated user."""

    try:
        summary = services.create_summary_service().execute(str(context.user.id))
    except WhoopConnectionNotFound:
        return None

    return WhoopSummary.model_validate(
        {
            key: value
            for key, value in summary.items()
            if key not in {"connected", "detail"}
        }
    )
