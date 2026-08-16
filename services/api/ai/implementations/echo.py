"""Development implementation for exercising the Coach API contracts."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

from django.conf import settings

from ai.runner import (
    CoachRunner,
    CoachRunnerEvent,
    CoachRunRequest,
    CoachRunResult,
    RunCompleted,
    TextDelta,
    ThinkingChanged,
)


class EchoCoachRunner:
    """Briefly thinks, then echoes the user's message for development testing."""

    def __init__(self, *, thinking_seconds: float) -> None:
        """Configures the visible simulated thinking duration."""

        self.thinking_seconds = max(thinking_seconds, 0)

    async def run(self, request: CoachRunRequest) -> CoachRunResult:
        """Returns the supplied user content after a small simulated delay."""

        await asyncio.sleep(self.thinking_seconds)
        return CoachRunResult(content=request.content, ai_message_batch=[])

    async def stream(self, request: CoachRunRequest) -> AsyncIterator[CoachRunnerEvent]:
        """Streams generic progress before returning the supplied user content."""

        yield ThinkingChanged(active=True)
        await asyncio.sleep(self.thinking_seconds)
        yield ThinkingChanged(active=False)
        yield TextDelta(delta=request.content)
        yield RunCompleted(CoachRunResult(content=request.content, ai_message_batch=[]))

    async def maintain_memory(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Development runner does not persist AI memory."""


def create_echo_runner() -> CoachRunner:
    """Creates the deterministic development runner for message-contract testing."""

    return EchoCoachRunner(
        thinking_seconds=float(getattr(settings, "COACH_ECHO_THINK_SECONDS", 0.5))
    )
