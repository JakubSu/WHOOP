"""Report estimated token counts for persisted coach conversation turns."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import tiktoken
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pydantic_ai.messages import ModelRequest, UserPromptPart

from ai.implementations.pydantic_coach.history import select_context
from ai.runner import CoachConversationHistory, CoachHistoryTurn
from coach.models import CoachConversation, CoachMessage


def _encoding_for(model_name: str) -> tiktoken.Encoding:
    """Return the tokenizer used by the configured OpenAI model family."""

    # tiktoken maps the gpt-5- model prefix, including gpt-5.6-luna, to o200k_base.
    if model_name.lower().startswith("gpt-5"):
        return tiktoken.get_encoding("o200k_base")

    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("o200k_base")


def _count_tokens(encoding: tiktoken.Encoding, value: str) -> int:
    return len(encoding.encode(value, disallowed_special=()))


def _json_tokens(encoding: tiktoken.Encoding, value: Any) -> int:
    if value is None:
        return 0
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return _count_tokens(encoding, serialized)


_RAW_CATEGORIES = {
    "user-prompt": "raw_user_prompt_tokens",
    "text": "raw_assistant_text_tokens",
    "thinking": "raw_thinking_tokens",
    "tool-call": "raw_tool_call_tokens",
    "tool-return": "raw_tool_result_tokens",
}


def _raw_batch_categories(
    encoding: tiktoken.Encoding, batch: list[dict[str, Any]] | None
) -> dict[str, int]:
    """Estimate the saved model-message batch by durable protocol category."""

    categories = {
        "raw_user_prompt_tokens": 0,
        "raw_assistant_text_tokens": 0,
        "raw_thinking_tokens": 0,
        "raw_tool_call_tokens": 0,
        "raw_tool_result_tokens": 0,
        "raw_other_part_tokens": 0,
    }
    raw_context_tokens = _json_tokens(encoding, batch)
    for message in batch or []:
        for part in message.get("parts", []):
            category = _RAW_CATEGORIES.get(
                part.get("part_kind"), "raw_other_part_tokens"
            )
            categories[category] += _json_tokens(encoding, part)
    categories["raw_protocol_tokens"] = raw_context_tokens - sum(categories.values())
    categories["raw_context_tokens"] = raw_context_tokens
    return categories


def _tool_activity(batch: list[dict[str, Any]] | None) -> dict[str, int]:
    """Count tool calls and the model-response rounds that made them."""

    tool_call_count = 0
    tool_round_count = 0
    for message in batch or []:
        calls_in_message = sum(
            part.get("part_kind") == "tool-call" for part in message.get("parts", [])
        )
        tool_call_count += calls_in_message
        # A model response can request several tools in parallel, but that is one round.
        if calls_in_message:
            tool_round_count += 1
    return {
        "tool_call_count": tool_call_count,
        "tool_round_count": tool_round_count,
    }


def _current_run_input_tokens(
    encoding: tiktoken.Encoding, batch: list[dict[str, Any]] | None, user_tokens: int
) -> tuple[int, int]:
    """Estimate the current-run input carried into each model request.

    Each saved response follows the messages that were available when that
    request was made. The saved batch does not include the prior conversation;
    that is accounted for separately by ``_history_tokens``.
    """

    response_positions = [
        index for index, message in enumerate(batch or []) if message.get("kind") == "response"
    ]
    if not response_positions:
        return user_tokens, 1
    return (
        sum(_json_tokens(encoding, (batch or [])[:index]) for index in response_positions),
        len(response_positions),
    )


def _provider_request_inputs(batch: list[dict[str, Any]] | None) -> list[int]:
    """Return the authoritative provider input count for each saved response."""

    inputs: list[int] = []
    for message in batch or []:
        usage = message.get("usage")
        if message.get("kind") != "response" or not isinstance(usage, dict):
            continue
        input_tokens = usage.get("input_tokens")
        if isinstance(input_tokens, int):
            inputs.append(input_tokens)
    return inputs


def _context_input_estimate(
    history_turns: list[CoachHistoryTurn], user_content: str
) -> int | None:
    """Reproduce the context-selection estimate emitted to Logfire."""

    if not history_turns:
        return None
    base_messages = [ModelRequest(parts=[UserPromptPart(content=user_content)])]
    selection = select_context(
        history=CoachConversationHistory(turns=history_turns),
        base_messages=base_messages,
        token_limit=(
            int(settings.COACH_MAX_INPUT_TOKENS_PER_REQUEST)
            - int(settings.COACH_CONTEXT_TOKEN_RESERVE)
        ),
    )
    return selection.input_tokens


def _preview(content: str, length: int = 10) -> str:
    """Return a compact single-line label for the human-readable table."""

    return " ".join(content.split())[:length]


def _turn_rows(
    conversations: Iterable[CoachConversation], encoding: tiktoken.Encoding
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for conversation in conversations:
        pending_user: CoachMessage | None = None
        turn_number = 0
        prior_turns: list[CoachHistoryTurn] = []
        messages = CoachMessage.objects.filter(conversation=conversation).only(
            "id", "role", "content", "ai_message_batch", "created_at"
        ).order_by("created_at", "id")
        for message in messages:
            if message.role == CoachMessage.Role.USER:
                pending_user = message
                continue
            if (
                message.role != CoachMessage.Role.ASSISTANT
                or pending_user is None
                or message.ai_message_batch is None
            ):
                continue

            turn_number += 1
            user_tokens = _count_tokens(encoding, pending_user.content)
            assistant_tokens = _count_tokens(encoding, message.content)
            tool_activity = _tool_activity(message.ai_message_batch)
            provider_inputs = _provider_request_inputs(message.ai_message_batch)
            raw_start = max(0, len(prior_turns) - int(settings.COACH_CONTEXT_RECENT_TURNS))
            history_per_request = _context_input_estimate(
                [
                    CoachHistoryTurn(
                        user_content=turn.user_content,
                        assistant_content=turn.assistant_content,
                        raw_batch=turn.raw_batch if index >= raw_start else None,
                    )
                    for index, turn in enumerate(prior_turns)
                ],
                pending_user.content,
            )
            if provider_inputs:
                request_count = len(provider_inputs)
                total_tokens = sum(provider_inputs)
                max_per_request_tokens = max(provider_inputs)
            else:
                current_run_tokens, request_count = _current_run_input_tokens(
                    encoding, message.ai_message_batch, user_tokens
                )
                total_tokens = current_run_tokens
                max_per_request_tokens = current_run_tokens
            # ``context_provider_input_tokens`` is calculated once when the
            # context is composed, before the agent starts making requests.
            # It is not a provider measurement for every request, so scaling
            # it by ``request_count`` produces a number Logfire never reports.
            history_tokens_per_request = history_per_request or 0
            history_total_tokens = history_tokens_per_request
            rows.append(
                {
                    "turn": turn_number,
                    "created_at": message.created_at.isoformat(),
                    "user_message_preview": _preview(pending_user.content),
                    "user_tokens": user_tokens,
                    "assistant_tokens": assistant_tokens,
                    "history_total_tokens": history_total_tokens,
                    "history_per_request_avg_tokens": history_tokens_per_request,
                    "total_tokens": total_tokens,
                    "total_per_request_avg_tokens": total_tokens // request_count,
                    "max_per_request_tokens": max_per_request_tokens,
                    "tool_call_count": tool_activity["tool_call_count"],
                    "request_count": request_count,
                }
            )
            prior_turns.append(
                CoachHistoryTurn(
                    user_content=pending_user.content,
                    assistant_content=message.content,
                    raw_batch=message.ai_message_batch,
                )
            )
            pending_user = None
    return sorted(rows, key=lambda row: row["created_at"], reverse=True)


class Command(BaseCommand):
    help = "Analyze estimated token counts for every saved coach conversation turn."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--conversation",
            "--conversation-id",
            dest="conversation_id",
            help="Analyze one conversation UUID instead of all saved conversations.",
        )
        parser.add_argument(
            "--format",
            choices=("table", "json", "csv"),
            default="table",
            help="Report format (default: table).",
        )
        parser.add_argument("--output", help="Optional file path for the report.")

    def handle(self, *args: Any, **options: Any) -> None:
        model_name = str(settings.OPENAI_MODEL)
        encoding = _encoding_for(model_name)
        conversations = CoachConversation.objects.all()
        if conversation_id := options["conversation_id"]:
            conversations = conversations.filter(id=conversation_id)
            if not conversations.exists():
                raise CommandError(f"Conversation {conversation_id} was not found.")

        rows = _turn_rows(conversations, encoding)
        report_format = options["format"]
        report = self._render(rows, report_format, model_name, encoding.name)
        output_path = options.get("output")
        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8", newline="")
            self.stdout.write(f"Wrote {len(rows)} saved turns to {path}")
        else:
            self.stdout.write(report, ending="" if report.endswith("\n") else "\n")

    def _render(
        self, rows: list[dict[str, Any]], report_format: str, model_name: str, encoding_name: str
    ) -> str:
        if report_format == "json":
            return json.dumps(
                {
                    "tokenizer": encoding_name,
                    "model": model_name,
                    "turn_count": len(rows),
                    "totals": _totals(rows),
                    "turns": rows,
                },
                indent=2,
            ) + "\n"
        if report_format == "csv":
            fieldnames = list(rows[0]) if rows else _fieldnames()
            from io import StringIO

            buffer = StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            return buffer.getvalue()
        return _table(rows, model_name, encoding_name)


def _fieldnames() -> list[str]:
    return [
        "created_at", "user_message_preview", "turn", "user_tokens", "assistant_tokens", "history_total_tokens",
        "history_per_request_avg_tokens", "total_tokens", "total_per_request_avg_tokens",
        "max_per_request_tokens", "tool_call_count", "request_count",
    ]


def _totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(row[field] for row in rows)
        for field in (
            "user_tokens", "assistant_tokens", "history_total_tokens", "total_tokens", "max_per_request_tokens",
            "tool_call_count", "request_count",
        )
    }


def _table(rows: list[dict[str, Any]], model_name: str, encoding_name: str) -> str:
    headers = (
        "date", "message", "turn", "user", "assistant", "history total", "history / request",
        "total", "total / request", "max / request", "tool calls", "rounds (requests)",
    )
    body = [
        (
            row["created_at"][:19], row["user_message_preview"], str(row["turn"]),
            str(row["user_tokens"]), str(row["assistant_tokens"]),
            str(row["history_total_tokens"]),
            str(row["history_per_request_avg_tokens"]), str(row["total_tokens"]),
            str(row["total_per_request_avg_tokens"]), str(row["max_per_request_tokens"]),
            str(row["tool_call_count"]),
            str(row["request_count"]),
        )
        for row in rows
    ]
    totals = _totals(rows)
    body.append((
        "", "TOTAL", str(len(rows)), str(totals["user_tokens"]), str(totals["assistant_tokens"]),
        str(totals["history_total_tokens"]), "-", str(totals["total_tokens"]),
        str(totals["total_tokens"] // max(1, totals["request_count"])),
        str(max((row["max_per_request_tokens"] for row in rows), default=0)),
        str(totals["tool_call_count"]), str(totals["request_count"]),
    ))
    widths = [max(len(header), *(len(row[index]) for row in body)) for index, header in enumerate(headers)]
    lines = [f"Tokenizer: {encoding_name} (requested model: {model_name})", ""]
    lines.append("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    lines.append("  ".join("-" * width for width in widths))
    lines.extend("  ".join(value.rjust(widths[index]) for index, value in enumerate(row)) for row in body)
    lines.append("")
    lines.append("total uses the provider input counts saved on each model response, so it should match Logfire exactly")
    lines.append("history total is the one-time context-selection estimate emitted as context_provider_input_tokens in Logfire")
    lines.append("history / request repeats that estimate; the provider does not expose an exact history-only count per request.")
    lines.append("Provider usage does not separately report history, instructions, tool definitions, or the current prompt.")
    return "\n".join(lines) + "\n"
