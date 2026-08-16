"""Bounded, private conversation memory and historical tool projection."""

from __future__ import annotations

import copy
import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_ITEMS = 20
MAX_TEXT_LENGTH = 280
MAX_SEARCH_RESULTS = 5
MAX_WORKOUT_EXERCISES = 20


class ExerciseReference(BaseModel):
    id: str
    name: str = Field(max_length=120)
    details: str = Field(default="", max_length=MAX_TEXT_LENGTH)


class WorkoutReference(BaseModel):
    id: str
    name: str = Field(max_length=120)
    date: str = Field(default="", max_length=32)
    details: str = Field(default="", max_length=MAX_TEXT_LENGTH)


class ConversationMemory(BaseModel):
    """Validated durable facts retained when raw turns age out."""

    version: int = 1
    user_preferences: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    decisions: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    exercise_references: list[ExerciseReference] = Field(
        default_factory=list, max_length=MAX_ITEMS
    )
    workout_references: list[WorkoutReference] = Field(
        default_factory=list, max_length=MAX_ITEMS
    )
    recommendation_changes: list[str] = Field(
        default_factory=list, max_length=MAX_ITEMS
    )
    unresolved_requests: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)

    @field_validator(
        "user_preferences",
        "decisions",
        "recommendation_changes",
        "unresolved_requests",
        mode="before",
    )
    @classmethod
    def _bound_text_items(cls, value: Any) -> list[str]:
        return [str(item).strip()[:MAX_TEXT_LENGTH] for item in value or [] if str(item).strip()][
            :MAX_ITEMS
        ]

    @classmethod
    def from_storage(cls, value: Any) -> "ConversationMemory":
        return cls.model_validate(value or {})

    def prompt_json(self) -> str:
        return self.model_dump_json(exclude_defaults=True)


def project_batch_for_prompt(batch: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Return a compact copy of one persisted batch without changing the audit copy."""

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


def estimate_tokens(value: Any) -> int:
    """Conservatively select whole batches; provider preflight is the exact guard."""

    serialized = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return max(1, (len(serialized.encode("utf-8")) + 1) // 2)


def _compact_tool_result(tool_name: str, content: Any) -> Any:
    value = _json_content(content)
    if tool_name in {"search_exercises", "search_workouts"} and isinstance(value, list):
        return [_select_fields(item, ("id", "name", "date", "prescription_type", "muscle_group")) for item in value[:MAX_SEARCH_RESULTS]]
    if tool_name == "get_exercise" and isinstance(value, dict):
        return _select_fields(value, ("id", "name", "prescription_type", "muscle_group", "found", "message"))
    if tool_name == "get_workout" and isinstance(value, dict):
        compact = _select_fields(value, ("id", "name", "date", "expected_time", "found", "message"))
        exercises = value.get("exercises")
        if isinstance(exercises, list):
            compact["exercises"] = [
                _select_fields(item, ("workout_exercise_id", "exercise_id", "name", "position", "sets", "reps", "time"))
                for item in exercises[:MAX_WORKOUT_EXERCISES]
            ]
        return compact
    if tool_name == "get_whoop_summary" and isinstance(value, dict):
        return {key: value[key] for key in sorted(value) if key not in {"detail", "connected"}}
    if tool_name in {"create_recommendation", "get_active_recommendation", "request_ui_action"}:
        if isinstance(value, dict):
            return _select_fields(value, ("id", "recommendation_id", "status", "accepted", "message", "summary"))
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
        return {"value": str(value)[:MAX_TEXT_LENGTH]}
    return {field: value[field] for field in fields if field in value}
