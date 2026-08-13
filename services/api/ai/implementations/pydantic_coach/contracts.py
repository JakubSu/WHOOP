"""Private contracts owned by the Pydantic AI Coach adapter."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from ai.runner import CoachActivity


@dataclass(frozen=True)
class CoachRuntimeLimits:
    """Validated per-run limits loaded from trusted Django settings."""

    history_max_batches: int
    history_max_tokens: int
    request_limit: int
    tool_calls_limit: int
    input_tokens_limit: int
    output_tokens_limit: int
    per_request_input_tokens_limit: int
    cost_limit_usd: Decimal
    tool_timeout_seconds: float

    def __post_init__(self) -> None:
        for name in (
            "history_max_batches",
            "history_max_tokens",
            "request_limit",
            "tool_calls_limit",
            "input_tokens_limit",
            "output_tokens_limit",
            "per_request_input_tokens_limit",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than zero.")
        if self.cost_limit_usd <= 0:
            raise ValueError("cost_limit_usd must be greater than zero.")
        if self.tool_timeout_seconds <= 0:
            raise ValueError("tool_timeout_seconds must be greater than zero.")


@dataclass
class CoachRunState:
    """Mutable run-local state that the model cannot supply or alter directly."""

    activity_sink: Callable[[CoachActivity], None]
    activities: dict[str, CoachActivity] = field(default_factory=dict)
    recommendation_id: uuid.UUID | None = None

    def publish(self, activity: CoachActivity) -> None:
        self.activities[activity.id] = activity
        self.activity_sink(activity)

    def fail_running(self) -> list[CoachActivity]:
        """Marks unfinished activities terminal without publishing duplicate events."""

        failed: list[CoachActivity] = []
        for activity in self.activities.values():
            if activity.status == "running":
                terminal = CoachActivity(
                    id=activity.id,
                    kind=activity.kind,
                    label=activity.label,
                    status="failed",
                )
                self.activities[terminal.id] = terminal
                failed.append(terminal)
        return failed


@dataclass(frozen=True)
class CoachDeps:
    """Trusted application state injected into every agent run and tool call."""

    user: Any
    conversation: Any
    run_id: uuid.UUID
    limits: CoachRuntimeLimits
    state: CoachRunState
