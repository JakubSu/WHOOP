"""Authenticated context passed explicitly to every AI tool."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from coach.models import CoachConversation


@dataclass(frozen=True)
class CoachToolContext:
    """Scopes one tool call to a user, conversation, run, and retry-safe call ID."""

    user: Any
    conversation: CoachConversation
    run_id: uuid.UUID
    tool_call_id: str
