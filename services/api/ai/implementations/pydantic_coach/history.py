"""Provider-counted context composition for persisted Coach conversations."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from ai.runner import CoachConversationHistory, CoachHistoryTurn

MAX_SEARCH_RESULTS = 3
MAX_WORKOUT_EXERCISES = 12


@dataclass(frozen=True)
class ContextSelection:
    messages: list[ModelMessage]
    input_tokens: int
    raw_turn_count: int
    visible_turn_count: int
    dropped_turn_count: int


def select_context(
    *,
    history: CoachConversationHistory,
    base_messages: list[ModelMessage],
    token_limit: int,
    estimate: Callable[[list[ModelMessage]], int] | None = None,
) -> ContextSelection:
    """Choose the richest chronological complete turns under a local estimate.

    This deliberately avoids a provider round trip for every candidate turn. The
    result is an estimate only: the provider remains authoritative for actual
    usage and the runner's hard limits.
    """

    estimate = estimate or estimate_messages_tokens
    selected: list[list[ModelMessage]] = []
    raw_turn_count = 0
    visible_turn_count = 0
    dropped_turn_count = 0

    for turn in reversed(history.turns):
        chosen: tuple[list[ModelMessage], bool] | None = None
        for messages, is_raw in _representations(turn):
            candidate = [
                *messages,
                *[item for chunk in selected for item in chunk],
                *base_messages,
            ]
            if estimate(candidate) <= token_limit:
                chosen = (messages, is_raw)
                break
        if chosen is None:
            dropped_turn_count += 1
            break
        messages, is_raw = chosen
        selected.insert(0, messages)
        if is_raw:
            raw_turn_count += 1
        else:
            visible_turn_count += 1

    messages = [item for chunk in selected for item in chunk]
    messages.extend(base_messages)
    input_tokens = estimate(messages)
    if input_tokens > token_limit:
        raise ValueError(
            "Coach instructions and the current user message exceed the context limit."
        )
    return ContextSelection(
        messages=messages,
        input_tokens=input_tokens,
        raw_turn_count=raw_turn_count,
        visible_turn_count=visible_turn_count,
        dropped_turn_count=dropped_turn_count,
    )


def estimate_messages_tokens(messages: list[ModelMessage]) -> int:
    """Fast conservative estimate for serialized text/protocol context.

    English prose often averages about four bytes per token. Three bytes gives
    us a small safety margin for JSON punctuation, identifiers, and non-English
    text while keeping history selection entirely local.
    """

    from pydantic_ai.messages import ModelMessagesTypeAdapter

    serialized = ModelMessagesTypeAdapter.dump_python(messages, mode="json")
    return estimate_tokens(serialized)


def estimate_tokens(value: Any) -> int:
    """Estimate tokens from compact JSON without calling the model provider."""

    serialized = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return max(1, (len(serialized.encode("utf-8")) + 2) // 3)


def _representations(turn: CoachHistoryTurn) -> list[tuple[list[ModelMessage], bool]]:
    visible = [
        ModelRequest(parts=[UserPromptPart(content=turn.user_content)]),
        ModelResponse(parts=[TextPart(content=turn.assistant_content)]),
    ]
    if turn.raw_batch is None:
        return [(visible, False)]
    projected, _ = project_batch_for_prompt(turn.raw_batch)
    from pydantic_ai.messages import ModelMessagesTypeAdapter

    return [
        (ModelMessagesTypeAdapter.validate_python(projected), True),
        (visible, False),
    ]


def project_batch_for_prompt(
    batch: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Compact tool-result payloads in a copy, retaining protocol identifiers."""

    projected = copy.deepcopy(batch)
    compacted = 0
    for message in projected:
        for part in message.get("parts", []):
            if part.get("part_kind") != "tool-return":
                continue
            content = part.get("content")
            replacement = _compact_tool_result(part.get("tool_name", ""), content)
            if replacement != content:
                part["content"] = replacement
                compacted += 1
    return projected, compacted


def _compact_tool_result(tool_name: str, content: Any) -> Any:
    value = _json_content(content)
    if tool_name in {"search_exercises", "search_workouts"} and isinstance(value, list):
        return [
            _select_fields(item, ("id", "name", "date"))
            for item in value[:MAX_SEARCH_RESULTS]
        ]
    if tool_name == "get_exercise" and isinstance(value, dict):
        return _select_fields(
            value, ("id", "name", "prescription_type", "muscle_group", "found")
        )
    if tool_name == "get_workout" and isinstance(value, dict):
        compact = _select_fields(
            value, ("id", "name", "date", "expected_time", "found")
        )
        if isinstance(value.get("exercises"), list):
            compact["exercises"] = [
                _select_fields(
                    item,
                    (
                        "workout_exercise_id",
                        "exercise_id",
                        "name",
                        "position",
                        "sets",
                        "reps",
                        "time",
                    ),
                )
                for item in value["exercises"][:MAX_WORKOUT_EXERCISES]
            ]
        return compact
    return content


def _json_content(content: Any) -> Any:
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content


def _select_fields(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"value": str(value)[:280]}
    return {field: value[field] for field in fields if field in value}
