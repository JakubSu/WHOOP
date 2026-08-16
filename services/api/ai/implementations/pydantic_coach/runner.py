"""Adapter from Pydantic AI v2 events to the owned Coach runner contract."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from pydantic_ai import Agent, AgentRunResultEvent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessagesTypeAdapter,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ToolReturnPart,
)
from pydantic_ai.usage import UsageLimits

from ai.runner import (
    ActivityChanged,
    CoachActivity,
    CoachRunnerEvent,
    CoachRunRequest,
    CoachRunResult,
    RunCompleted,
    RunFailed,
    TextDelta,
    ThinkingChanged,
)
from coach.models import CoachConversation

from .agent import create_coach_agent
from .contracts import CoachDeps, CoachRunState, CoachRuntimeLimits
from .tools import activity_for_tool

logger = logging.getLogger(__name__)


class PydanticCoachRunner:
    """Runs one typed Pydantic AI Coach turn through the async runner protocol."""

    def __init__(
        self, *, limits: CoachRuntimeLimits, model_name: str, timeout_seconds: float
    ) -> None:
        self._limits = limits
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._agent: Agent[CoachDeps, str] = create_coach_agent(
            model_name=model_name,
            tool_timeout_seconds=limits.tool_timeout_seconds,
        )

    async def run(self, request: CoachRunRequest) -> CoachRunResult:
        """Run to completion for the non-streaming Coach endpoint."""

        async for event in self.stream(request):
            if isinstance(event, RunCompleted):
                return event.result
            if isinstance(event, RunFailed):
                raise TypeError(f"Pydantic Coach run failed: {event.code}")
        raise RuntimeError("Pydantic Coach run ended without a completion event.")

    async def stream(self, request: CoachRunRequest) -> AsyncIterator[CoachRunnerEvent]:
        """Map native Pydantic AI events into the owned async event protocol."""

        user = await asyncio.to_thread(get_user_model().objects.get, pk=request.user_id)
        conversation = await asyncio.to_thread(
            CoachConversation.objects.get,
            pk=request.conversation_id,
            user_id=request.user_id,
        )
        activity_events: asyncio.Queue[ActivityChanged] = asyncio.Queue()
        state = CoachRunState(
            activity_sink=lambda activity: activity_events.put_nowait(
                ActivityChanged(activity=activity)
            )
        )
        deps = CoachDeps(
            user=user,
            conversation=conversation,
            run_id=request.run_id,
            limits=self._limits,
            state=state,
        )
        history = _restore_history(request.ai_message_batches, self._limits)
        usage_limits = UsageLimits(
            request_limit=self._limits.request_limit,
            tool_calls_limit=self._limits.tool_calls_limit,
            input_tokens_limit=self._limits.input_tokens_limit,
            output_tokens_limit=self._limits.output_tokens_limit,
            per_request_input_tokens_limit=self._limits.per_request_input_tokens_limit,
            # Not every supported Pydantic AI model implements preflight token
            # counting. The bounded persisted history and request serializer are
            # the pre-request guard; UsageLimits still enforce measured usage.
            count_tokens_before_request=False,
            cost_limit=self._limits.cost_limit_usd,
        )
        yield ThinkingChanged(active=True)
        thinking_active = True
        result: Any = None
        emitted_text = False
        started_at = time.monotonic()
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with self._agent.run_stream_events(
                    request.content,
                    deps=deps,
                    message_history=history,
                    run_id=str(request.run_id),
                    conversation_id=str(request.conversation_id),
                    usage_limits=usage_limits,
                ) as events:
                    event_iterator = aiter(events)
                    event_task = asyncio.ensure_future(anext(event_iterator))
                    activity_task = asyncio.create_task(activity_events.get())
                    try:
                        while True:
                            done, _ = await asyncio.wait(
                                {event_task, activity_task},
                                return_when=asyncio.FIRST_COMPLETED,
                            )
                            if activity_task in done:
                                yield activity_task.result()
                                activity_task = asyncio.create_task(
                                    activity_events.get()
                                )
                            if event_task in done:
                                try:
                                    event = event_task.result()
                                except StopAsyncIteration:
                                    break
                                event_task = asyncio.ensure_future(anext(event_iterator))
                                logger.info(
                                    "event_type=%s event=%s",
                                    type(event).__name__,
                                    event,
                                )
                                activity = _activity_from_native_event(event)
                                if activity is not None:
                                    state.publish(activity)
                                if isinstance(event, PartStartEvent) and isinstance(
                                    event.part, ThinkingPart
                                ):
                                    if not thinking_active:
                                        yield ThinkingChanged(active=True)
                                        thinking_active = True
                                elif isinstance(event, PartStartEvent) and isinstance(
                                    event.part, TextPart
                                ):
                                    if thinking_active:
                                        yield ThinkingChanged(active=False)
                                        thinking_active = False
                                    if event.part.content:
                                        emitted_text = True
                                        yield TextDelta(delta=event.part.content)
                                elif isinstance(event, PartDeltaEvent) and isinstance(
                                    event.delta, TextPartDelta
                                ):
                                    if thinking_active:
                                        yield ThinkingChanged(active=False)
                                        thinking_active = False
                                    if event.delta.content_delta:
                                        emitted_text = True
                                        yield TextDelta(delta=event.delta.content_delta)
                                elif isinstance(event, AgentRunResultEvent):
                                    result = event.result
                    finally:
                        for task in (event_task, activity_task):
                            task.cancel()
                        await asyncio.gather(
                            event_task, activity_task, return_exceptions=True
                        )

                    if result is None:
                        raise RuntimeError(
                            "Pydantic Coach stream ended without a result."
                        )
                    ai_message_batch = ModelMessagesTypeAdapter.dump_python(
                        events.new_messages(), mode="json"
                    )
                    _log_usage(events.usage, run_id=request.run_id)
        except TimeoutError:
            running = [
                str(activity.id)
                for activity in state.activities.values()
                if activity.status == "running"
            ]
            logger.warning(
                "coach_run_timeout run_id=%s timeout_seconds=%s elapsed_ms=%s active_activity_ids=%s",
                request.run_id,
                self._timeout_seconds,
                round((time.monotonic() - started_at) * 1000),
                running,
            )
            for activity in state.fail_running():
                yield ActivityChanged(activity)
            if thinking_active:
                yield ThinkingChanged(active=False)
            yield RunFailed(code="timeout", retryable=True)
            return
        except asyncio.CancelledError:
            state.fail_running()
            logger.info("coach_run_cancelled run_id=%s", request.run_id)
            raise
        except Exception as exc:  # noqa: BLE001 - normalized into the runner protocol
            logger.warning(
                "coach_run_error run_id=%s elapsed_ms=%s error_type=%s error=%s",
                request.run_id,
                round((time.monotonic() - started_at) * 1000),
                type(exc).__name__,
                str(exc),
            )
            for activity in state.fail_running():
                yield ActivityChanged(activity)
            if thinking_active:
                yield ThinkingChanged(active=False)
            yield RunFailed(code="coach_run_failed", retryable=True)
            return

        logger.info(
            "coach_run_completed run_id=%s elapsed_ms=%s activity_count=%s",
            request.run_id,
            round((time.monotonic() - started_at) * 1000),
            len(state.activities),
        )
        while not activity_events.empty():
            yield activity_events.get_nowait()
        terminal_activities = [
            activity
            for activity in state.activities.values()
            if activity.status in {"completed", "failed"}
        ]
        if thinking_active:
            yield ThinkingChanged(active=False)
        # Plain text output arrives as TextPart deltas. Retain this fallback for
        # models/tests that return a completed result without a text delta.
        if not emitted_text:
            yield TextDelta(delta=result.output)
        yield RunCompleted(
            CoachRunResult(
                content=result.output,
                ai_message_batch=ai_message_batch,
                activities=terminal_activities,
                recommendation_id=state.recommendation_id,
                ui_actions=state.ui_actions,
            )
        )


def _activity_from_native_event(event: Any) -> CoachActivity | None:
    """Maps Pydantic AI function-tool lifecycle events into owned activities."""

    if isinstance(event, FunctionToolCallEvent):
        activity = activity_for_tool(
            event.part.tool_name, event.part.tool_call_id, "running"
        )
        return activity
    if isinstance(event, FunctionToolResultEvent):
        part = event.part
        status = (
            "completed"
            if isinstance(part, ToolReturnPart) and part.outcome == "success"
            else "failed"
        )
        activity = activity_for_tool(part.tool_name or "", part.tool_call_id, status)
        return activity
    return None


def create_pydantic_coach_runner() -> PydanticCoachRunner:
    """Build the explicit production runner from trusted Django settings."""

    return PydanticCoachRunner(
        model_name=str(settings.OPENAI_MODEL),
        timeout_seconds=float(settings.OPENAI_TIMEOUT),
        limits=CoachRuntimeLimits(
            history_max_batches=int(settings.COACH_HISTORY_MAX_BATCHES),
            history_max_tokens=int(settings.COACH_HISTORY_MAX_TOKENS),
            request_limit=int(settings.COACH_MAX_MODEL_REQUESTS),
            tool_calls_limit=int(settings.COACH_MAX_TOOL_CALLS),
            input_tokens_limit=int(settings.COACH_MAX_INPUT_TOKENS),
            output_tokens_limit=int(settings.COACH_MAX_OUTPUT_TOKENS),
            per_request_input_tokens_limit=int(
                settings.COACH_MAX_INPUT_TOKENS_PER_REQUEST
            ),
            cost_limit_usd=Decimal(str(settings.COACH_MAX_COST_USD)),
            tool_timeout_seconds=float(settings.COACH_TOOL_TIMEOUT_SECONDS),
        ),
    )


def _restore_history(
    batches: list[list[dict[str, Any]]], limits: CoachRuntimeLimits
) -> list[Any]:
    """Restore recent, private Pydantic message batches under a byte/token budget."""

    selected: list[list[dict[str, Any]]] = []
    total_bytes = 0
    max_bytes = limits.history_max_tokens * 4
    for batch in reversed(batches[-limits.history_max_batches :]):
        size = len(json.dumps(batch, separators=(",", ":")).encode("utf-8"))
        if selected and total_bytes + size > max_bytes:
            break
        selected.append(batch)
        total_bytes += size
    messages: list[Any] = []
    for batch in reversed(selected):
        messages.extend(ModelMessagesTypeAdapter.validate_python(batch))
    return messages


def _log_usage(usage: Any, *, run_id: Any) -> None:
    """Record aggregate operational data without content, prompts, or tool payloads."""

    logger.info(
        "coach_run_usage run_id=%s requests=%s tool_calls=%s input_tokens=%s output_tokens=%s cost_usd=%s",
        run_id,
        usage.requests,
        usage.tool_calls,
        usage.input_tokens,
        usage.output_tokens,
        usage.cost,
    )
