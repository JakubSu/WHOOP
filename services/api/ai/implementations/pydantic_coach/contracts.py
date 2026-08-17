"""Private contracts owned by the Pydantic AI Coach adapter."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from ai.runner import CoachActivity, CoachConversationHistory
from coach.contracts.ui_actions import UiActionDraft
from coach.view_context import CoachViewContext


@dataclass(frozen=True)
class CoachRuntimeLimits:
    """Validated per-run limits loaded from trusted Django settings."""

    recent_turns: int
    context_token_reserve: int
    request_limit: int
    tool_calls_limit: int
    input_tokens_limit: int
    output_tokens_limit: int
    per_request_input_tokens_limit: int
    cost_limit_usd: Decimal
    tool_timeout_seconds: float

    def __post_init__(self) -> None:
        for name in (
            "recent_turns",
            "context_token_reserve",
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
        if self.context_token_reserve >= self.per_request_input_tokens_limit:
            raise ValueError(
                "context_token_reserve must be smaller than per_request_input_tokens_limit."
            )


@dataclass
class CoachRunState:
    """Mutable run-local state that the model cannot supply or alter directly."""

    activity_sink: Callable[[CoachActivity], None]
    activities: dict[str, CoachActivity] = field(default_factory=dict)
    recommendation_id: uuid.UUID | None = None
    ui_actions: list[UiActionDraft] = field(default_factory=list)
    context_composed: bool = False
    context_input_tokens: int | None = None
    context_raw_turn_count: int = 0
    context_visible_turn_count: int = 0
    context_dropped_turn_count: int = 0

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

    def request_ui_action(self, action: UiActionDraft) -> None:
        """Records validated UI metadata for persistence after a successful run."""
        self.ui_actions.append(action)


@dataclass(frozen=True)
class CoachDeps:
    """Trusted application state injected into every agent run and tool call."""

    user: Any
    conversation: Any
    run_id: uuid.UUID
    limits: CoachRuntimeLimits
    state: CoachRunState
    history: CoachConversationHistory = field(default_factory=CoachConversationHistory)
    view_context: CoachViewContext | None = None
