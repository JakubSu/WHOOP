"""Recommendation ledger write tool."""

from __future__ import annotations

from ai.tools.context import CoachToolContext
from ai.tools.contracts import ActiveRecommendation, CreatedRecommendation
from ai.tools.errors import ToolValidationError
from recommendation import services as recommendation_services
from recommendation.contracts import RecommendationDraft


def create_recommendation(
    context: CoachToolContext,
    *,
    draft: RecommendationDraft,
    replaces_recommendation_id: str | None = None,
) -> CreatedRecommendation:
    """Creates a validated recommendation ledger and returns only its identifier."""

    try:
        recommendation = recommendation_services.create_recommendation(
            user=context.user,
            conversation=context.conversation,
            draft=draft,
            run_id=context.run_id,
            tool_call_id=context.tool_call_id,
            replaces_recommendation_id=replaces_recommendation_id,
        )
    except (
        recommendation_services.RecommendationConflict,
        recommendation_services.RecommendationValidationError,
    ) as exc:
        raise ToolValidationError("Recommendation request could not be applied.") from exc
    return CreatedRecommendation(recommendation_id=recommendation.id)


def get_active_recommendation(
    context: CoachToolContext,
) -> ActiveRecommendation | None:
    """Returns the conversation's copyable pending proposal, if it has one."""

    try:
        return recommendation_services.get_active_recommendation(
            user=context.user,
            conversation=context.conversation,
        )
    except recommendation_services.RecommendationValidationError as exc:
        raise ToolValidationError("Recommendation request could not be applied.") from exc
