"""Pydantic AI adapters for the framework-independent Coach domain tools."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from asgiref.sync import sync_to_async
from pydantic_ai import Agent, ModelRetry, RunContext

from ai.runner import ActivityKind, ActivityStatus, CoachActivity
from ai.tools import (
    CoachToolContext,
    create_recommendation,
    get_active_recommendation,
    get_whoop_summary,
    get_workout,
    search_exercises,
    search_workouts,
)
from ai.tools.contracts import ExerciseSummary
from ai.tools.errors import ToolNotFoundError, ToolValidationError
from recommendation.contracts import RecommendationDraft
from training.models import Exercise

from .contracts import CoachDeps

_ACTIVITY_BY_TOOL: dict[str, tuple[ActivityKind, str]] = {
    "search_workouts": ("workout_data", "Looking up your workouts…"),
    "get_workout": ("workout_data", "Looking up that workout…"),
    "get_whoop_summary": ("recovery_data", "Fetching your recovery data…"),
    "search_exercises": ("training_data", "Searching your exercise library…"),
    "get_active_recommendation": (
        "recommendation",
        "Checking your active recommendation…",
    ),
    "create_recommendation": ("recommendation", "Preparing your recommendation…"),
}


def _tool_context(ctx: RunContext[CoachDeps]) -> CoachToolContext:
    return CoachToolContext(
        user=ctx.deps.user,
        conversation=ctx.deps.conversation,
        run_id=ctx.deps.run_id,
        tool_call_id=str(getattr(ctx, "tool_call_id", "unknown-tool-call")),
    )


def activity_for_tool(
    tool_name: str, tool_call_id: str, status: ActivityStatus
) -> CoachActivity | None:
    """Builds a user-safe activity for one registered Pydantic AI tool call."""

    presentation = _ACTIVITY_BY_TOOL.get(tool_name)
    if presentation is None:
        return None
    kind, label = presentation
    return CoachActivity(id=tool_call_id, kind=kind, label=label, status=status)


async def _call(ctx: RunContext[CoachDeps], function: Any, **kwargs: Any) -> Any:
    try:
        result = await sync_to_async(function, thread_sensitive=True)(
            _tool_context(ctx), **kwargs
        )
    except ToolNotFoundError:
        return {
            "found": False,
            "message": "That item is not available in this account.",
        }
    except ToolValidationError as exc:
        raise ModelRetry(
            "The requested recommendation was not valid. Check the available data and try again."
        ) from exc
    except Exception:
        raise
    return result


def register_tools(agent: Agent[CoachDeps, str]) -> None:
    """Register only the small, eagerly available Coach tool catalog."""

    @agent.tool(name="search_workouts")
    async def search_workouts_tool(
        ctx: RunContext[CoachDeps],
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 20,
    ) -> Any:
        """Search the authenticated user's workouts in an optional date range."""
        return await _call(
            ctx,
            search_workouts,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    @agent.tool(name="get_workout")
    async def get_workout_tool(ctx: RunContext[CoachDeps], workout_id: UUID) -> Any:
        """Get one authenticated user's workout by ID."""
        return await _call(ctx, get_workout, workout_id=workout_id)

    @agent.tool(name="get_whoop_summary")
    async def get_whoop_summary_tool(ctx: RunContext[CoachDeps]) -> Any:
        """Get the authenticated user's latest normalized WHOOP summary."""
        return await _call(ctx, get_whoop_summary)

    @agent.tool(name="search_exercises")
    async def search_exercises_tool(
        ctx: RunContext[CoachDeps],
        names: list[str] | None = None,
        muscle_groups: list[Exercise.MuscleGroup] | None = None,
        limit: int = 20,
    ) -> list[ExerciseSummary]:
        """Search the user's and shared exercise library."""
        return await _call(
            ctx,
            search_exercises,
            names=names,
            muscle_groups=muscle_groups,
            limit=limit,
        )

    @agent.tool(name="get_active_recommendation")
    async def get_active_recommendation_tool(ctx: RunContext[CoachDeps]) -> Any:
        """Get the current active proposal for this conversation, if one exists."""
        return await _call(ctx, get_active_recommendation)

    @agent.tool(name="create_recommendation", sequential=True)
    async def create_recommendation_tool(
        ctx: RunContext[CoachDeps],
        draft: RecommendationDraft,
        replaces_recommendation_id: str | None = None,
    ) -> Any:
        """Create a reversible recommendation proposal; never apply a workout change."""
        result = await _call(
            ctx,
            create_recommendation,
            draft=draft,
            replaces_recommendation_id=replaces_recommendation_id,
        )
        if getattr(result, "recommendation_id", None) is not None:
            ctx.deps.state.recommendation_id = result.recommendation_id
        return result
