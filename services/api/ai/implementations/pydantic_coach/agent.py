"""Factory for the Pydantic AI Coach agent."""

from __future__ import annotations

from django.utils import timezone
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities import ProcessHistory
from pydantic_ai.messages import ModelMessage

from .contracts import CoachDeps, CoachResponse
from .prompts import COACH_INSTRUCTIONS
from .tools import register_tools


def _keep_bounded_history(
    ctx: RunContext[CoachDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    """Keep recent messages under a conservative serialized-token approximation."""
    # The runner already bounds persisted turns. This is a second guard before each
    # request, including tool loops created within one run.
    retained = list(messages)
    approximate_limit = ctx.deps.limits.history_max_tokens * 4
    while len(retained) > 1 and len(repr(retained).encode("utf-8")) > approximate_limit:
        retained.pop(0)
    return retained


def create_coach_agent(
    *, model_name: str, tool_timeout_seconds: float
) -> Agent[CoachDeps, CoachResponse]:
    """Build a fresh typed agent so settings and tests cannot leak between runs."""
    agent: Agent[CoachDeps, CoachResponse] = Agent(
        f"openai:{model_name}",
        name="whoop_coach",
        deps_type=CoachDeps,
        output_type=CoachResponse,
        instructions=COACH_INSTRUCTIONS,
        retries={"tools": 1, "output": 1},
        tool_timeout=tool_timeout_seconds,
        capabilities=[ProcessHistory(_keep_bounded_history)],
        defer_model_check=True,
    )

    @agent.instructions
    def trusted_runtime_context(ctx: RunContext[CoachDeps]) -> str:
        return f"Today is {timezone.localdate().isoformat()}. You are coaching one authenticated user."

    @agent.output_validator
    def validate_output(ctx: RunContext[CoachDeps], output: CoachResponse) -> CoachResponse:
        if not output.content.strip():
            raise ModelRetry("Return a non-empty user-facing response.")
        if ctx.deps.state.recommendation_id is not None and output.outcome != "recommendation_proposed":
            raise ModelRetry("A recommendation proposal was created, so set outcome to recommendation_proposed.")
        return output

    register_tools(agent)
    return agent
