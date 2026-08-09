"""Safe result contract for the recommendation write tool."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from recommendation.contracts import ActiveRecommendation


class CreatedRecommendation(BaseModel):
    """Identifies the persisted recommendation created by a tool call."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: UUID


__all__ = ["ActiveRecommendation", "CreatedRecommendation"]
