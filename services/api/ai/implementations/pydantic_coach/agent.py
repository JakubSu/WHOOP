"""Factory for the Pydantic AI Coach agent."""

from __future__ import annotations

from django.utils import timezone
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities.hooks import Hooks
from pydantic_ai.models import ModelRequestContext

from .contracts import CoachDeps
from .history import select_context
from .prompts import COACH_INSTRUCTIONS
from .tools import register_tools


def create_coach_agent(
    *, model_name: str, tool_timeout_seconds: float
) -> Agent[CoachDeps, str]:
    """Build a fresh typed agent so settings and tests cannot leak between runs."""
    hooks = Hooks(before_model_request=_compose_context)
    agent: Agent[CoachDeps, str] = Agent(
        f"openai:{model_name}",
        name="whoop_coach",
        deps_type=CoachDeps,
        output_type=str,
        instructions=COACH_INSTRUCTIONS,
        retries={"tools": 1, "output": 1},
        tool_timeout=tool_timeout_seconds,
        defer_model_check=True,
        capabilities=[hooks],
    )

    @agent.instructions
    def trusted_runtime_context(ctx: RunContext[CoachDeps]) -> str:
        context_instruction = (
            ctx.deps.view_context.coach_instruction()
            if ctx.deps.view_context is not None
            else (
                "No training screen is currently selected. General coaching is allowed, "
                "but ask the user to open a workout or week before an ambiguous training change."
            )
        )
        return (
            f"Today is {timezone.localdate().isoformat()}. You are coaching one authenticated user. "
            f"{context_instruction}"
        )

    @agent.output_validator
    def validate_output(ctx: RunContext[CoachDeps], output: str) -> str:
        if not output.strip():
            raise ModelRetry("Return a non-empty user-facing response.")
        return output

    register_tools(agent)
    return agent


async def _compose_context(
    ctx: RunContext[CoachDeps], request_context: ModelRequestContext
) -> ModelRequestContext:
    """Select one provider-counted history projection for the initial request."""

    if ctx.deps.state.context_composed:
        return request_context
    if not ctx.deps.history.turns:
        ctx.deps.state.context_composed = True
        return request_context
    token_limit = (
        ctx.deps.limits.per_request_input_tokens_limit
        - ctx.deps.limits.context_token_reserve
    )
    selection = select_context(
        history=ctx.deps.history,
        base_messages=list(request_context.messages),
        token_limit=token_limit,
    )
    request_context.messages = selection.messages
    ctx.deps.state.context_composed = True
    ctx.deps.state.context_input_tokens = selection.input_tokens
    ctx.deps.state.context_raw_turn_count = selection.raw_turn_count
    ctx.deps.state.context_visible_turn_count = selection.visible_turn_count
    ctx.deps.state.context_dropped_turn_count = selection.dropped_turn_count
    return request_context
