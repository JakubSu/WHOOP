"""Recommendation ledger write tool."""

from __future__ import annotations

import logging

from ai.tools.context import CoachToolContext
from ai.tools.contracts import ActiveRecommendation, CreatedRecommendation
from ai.tools.errors import ToolValidationError
from recommendation import services as recommendation_services
from recommendation.contracts import RecommendationDraft

logger = logging.getLogger(__name__)


def create_recommendation(
    context: CoachToolContext,
    *,
    draft: RecommendationDraft,
) -> CreatedRecommendation:
    """Creates a validated proposal, atomically replacing any active proposal."""

    try:
        recommendation = recommendation_services.create_recommendation(
            user=context.user,
            conversation=context.conversation,
            draft=draft,
            run_id=context.run_id,
            tool_call_id=context.tool_call_id,
        )
    except (
        recommendation_services.RecommendationConflict,
        recommendation_services.RecommendationValidationError,
    ) as exc:
        logger.warning(
            "create_recommendation_rejected run_id=%s tool_call_id=%s "
            "conversation_id=%s supersedes_active=true operation_count=%s "
            "error_type=%s reason=%s",
            context.run_id,
            context.tool_call_id,
            context.conversation.id,
            len(draft.operations),
            type(exc).__name__,
            exc,
            extra={
                "run_id": str(context.run_id),
                "tool_call_id": context.tool_call_id,
                "conversation_id": str(context.conversation.id),
                "supersedes_active": True,
                "operation_count": len(draft.operations),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise ToolValidationError(str(exc)) from exc
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
        logger.warning(
            "get_active_recommendation_rejected run_id=%s tool_call_id=%s "
            "conversation_id=%s error_type=%s reason=%s",
            context.run_id,
            context.tool_call_id,
            context.conversation.id,
            type(exc).__name__,
            exc,
            extra={
                "run_id": str(context.run_id),
                "tool_call_id": context.tool_call_id,
                "conversation_id": str(context.conversation.id),
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        raise ToolValidationError(str(exc)) from exc
