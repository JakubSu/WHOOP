"""Framework-independent execution contract for coach-capable AI runners."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from django.conf import settings
from django.utils.module_loading import import_string

ActivityKind = Literal[
    "recovery_data", "training_data", "workout_data", "recommendation", "other"
]
ActivityStatus = Literal["running", "completed", "failed"]


@dataclass(frozen=True)
class CoachActivity:
    """A sanitized tool activity that is safe to persist and show to users."""

    id: uuid.UUID
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
class CoachRunRequest:
    """The API-owned input required to execute one coach turn."""

    run_id: uuid.UUID
    conversation_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    ai_message_batches: list[list[dict[str, Any]]]


@dataclass(frozen=True)
class CoachRunResult:
    """The final assistant output and private state produced by a coach turn."""

    content: str
    ai_message_batch: list[dict[str, Any]]
    activities: list[CoachActivity] = field(default_factory=list)
    recommendation_id: uuid.UUID | None = None


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
class Keepalive:
    """An internal signal used to keep an otherwise idle event stream open."""


CoachRunnerEvent = (
    TextDelta | ThinkingChanged | ActivityChanged | RunCompleted | Keepalive
)


class CoachRunner(Protocol):
    """The framework-independent interface implemented by a coach AI adapter."""

    def run(self, request: CoachRunRequest) -> CoachRunResult: ...

    def stream(self, request: CoachRunRequest) -> Iterable[CoachRunnerEvent]: ...


class CoachRunnerUnavailable(RuntimeError):
    """Raised when the Coach API is called without a configured runner."""


class UnavailableCoachRunner:
    """The default runner that reports the AI integration as unconfigured."""

    def run(self, request: CoachRunRequest) -> CoachRunResult:
        """Raises because no concrete AI adapter is configured."""

        raise CoachRunnerUnavailable("The coach agent is not configured.")

    def stream(self, request: CoachRunRequest) -> Iterable[CoachRunnerEvent]:
        """Raises because no concrete AI adapter is configured."""

        raise CoachRunnerUnavailable("The coach agent is not configured.")


def create_unavailable_runner() -> CoachRunner:
    """Creates the runner used when no concrete implementation is configured."""

    return UnavailableCoachRunner()


def get_coach_runner() -> CoachRunner:
    """Loads the configured coach runner implementation."""

    factory_path = getattr(
        settings, "COACH_RUNNER_FACTORY", "ai.runner.create_unavailable_runner"
    )
    factory = import_string(factory_path)
    return factory()
