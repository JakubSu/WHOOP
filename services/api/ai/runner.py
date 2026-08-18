"""Framework-independent execution contract for coach-capable AI runners."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal, Protocol

from django.conf import settings
from django.utils.module_loading import import_string

from coach.contracts.ui_actions import UiActionDraft
from coach.view_context import CoachViewContext

ActivityKind = Literal[
    "recovery_data", "training_data", "workout_data", "recommendation", "other"
]
ActivityStatus = Literal["running", "completed", "failed"]


@dataclass(frozen=True)
class CoachActivity:
    """A sanitized tool activity that is safe to persist and show to users."""

    id: str
    kind: ActivityKind
    label: str
    status: ActivityStatus

    def as_dict(self) -> dict[str, str]:
        """Converts the activity to its owned JSON-compatible representation."""

        return {
            "id": str(self.id),
            "kind": self.kind,
            "label": self.label,
            "status": self.status,
        }


@dataclass(frozen=True)
class CoachHistoryTurn:
    """One complete exchange with an optional model-protocol representation."""

    user_content: str
    assistant_content: str
    raw_batch: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class CoachConversationHistory:
    """Chronological complete turns used to construct one Coach prompt."""

    turns: list[CoachHistoryTurn] = field(default_factory=list)


@dataclass(frozen=True)
class CoachRunRequest:
    """The API-owned input required to execute one coach turn."""

    run_id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    history: CoachConversationHistory = field(default_factory=CoachConversationHistory)
    view_context: CoachViewContext | None = None


@dataclass(frozen=True)
class CoachRunResult:
    """The final assistant output and private state produced by a coach turn."""

    content: str
    ai_message_batch: list[dict[str, Any]]
    cost_usd: Decimal = Decimal(0)
    activities: list[CoachActivity] = field(default_factory=list)
    recommendation_id: uuid.UUID | None = None
    ui_actions: list[UiActionDraft] = field(default_factory=list)


@dataclass(frozen=True)
class TextDelta:
    """An incremental fragment of assistant text emitted during streaming."""

    delta: str


@dataclass(frozen=True)
class ThinkingChanged:
    """A signal that turns the generic user-facing thinking indicator on or off."""

    active: bool


# if more info about the thinking is needed in the future, we can add more fields to map pydantic ThinkingPart and ThinkingPartDelta


@dataclass(frozen=True)
class ActivityChanged:
    """A sanitized tool activity lifecycle update emitted during streaming."""

    activity: CoachActivity


@dataclass(frozen=True)
class RunCompleted:
    """The terminal streaming event carrying the authoritative completed result."""

    result: CoachRunResult


@dataclass(frozen=True)
class RunFailed:
    """The terminal streaming event describing a safely classed failed run."""

    code: str
    retryable: bool
    cost_usd: Decimal | None = None


CoachRunnerEvent = (
    TextDelta | ThinkingChanged | ActivityChanged | RunCompleted | RunFailed
)


class CoachRunner(Protocol):
    """The framework-independent interface implemented by a coach AI adapter."""

    async def run(self, request: CoachRunRequest) -> CoachRunResult: ...

    def stream(self, request: CoachRunRequest) -> AsyncIterable[CoachRunnerEvent]: ...


class CoachRunnerUnavailable(RuntimeError):
    """Raised when the Coach API is called without a configured runner."""


class CoachRunFailed(RuntimeError):
    """Carries a normalized failed-run result to non-streaming callers."""

    def __init__(self, failure: RunFailed) -> None:
        super().__init__(failure.code)
        self.failure = failure


class UnavailableCoachRunner:
    """The default runner that reports the AI integration as unconfigured."""

    async def run(self, request: CoachRunRequest) -> CoachRunResult:
        """Raises because no concrete AI adapter is configured."""

        raise CoachRunnerUnavailable("The coach agent is not configured.")

    async def stream(self, request: CoachRunRequest) -> AsyncIterator[CoachRunnerEvent]:
        """Raises because no concrete AI adapter is configured."""

        raise CoachRunnerUnavailable("The coach agent is not configured.")
        yield TextDelta(delta="")  # pragma: no cover - makes this an async generator


def create_unavailable_runner() -> CoachRunner:
    """Creates the runner used when no concrete implementation is configured."""

    return UnavailableCoachRunner()


_startup_coach_runner: CoachRunner | None = None


def _create_coach_runner() -> CoachRunner:
    """Construct the runner selected by the current settings."""

    factory_path = getattr(
        settings, "COACH_RUNNER_FACTORY", "ai.runner.create_unavailable_runner"
    )
    factory = import_string(factory_path)
    runner = factory()
    return runner


def initialize_coach_runner() -> CoachRunner:
    """Build the configured runner once during application startup."""

    global _startup_coach_runner
    if _startup_coach_runner is None:
        _startup_coach_runner = _create_coach_runner()
    return _startup_coach_runner


def get_coach_runner() -> CoachRunner:
    """Return the startup runner, or lazily build one outside app startup."""

    if _startup_coach_runner is not None:
        return _startup_coach_runner
    return _create_coach_runner()
