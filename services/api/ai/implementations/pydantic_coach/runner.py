"""Adapter from Pydantic AI v2 events to the owned Coach runner contract."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from pydantic_ai import Agent, AgentRunResultEvent, UsageLimitExceeded
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessagesTypeAdapter,
    ModelResponse,
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
from .observability import record_token_usage
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
            history=request.history,
            view_context=request.view_context,
        )
        usage_limits = UsageLimits(
            request_limit=self._limits.request_limit,
            tool_calls_limit=self._limits.tool_calls_limit,
            input_tokens_limit=self._limits.input_tokens_limit,
            output_tokens_limit=self._limits.output_tokens_limit,
            per_request_input_tokens_limit=self._limits.per_request_input_tokens_limit,
            count_tokens_before_request=False,
            cost_limit=self._limits.cost_limit_usd,
        )
        yield ThinkingChanged(active=True)
        thinking_active = True
        result: Any = None
        events: Any = None
        emitted_text = False
        started_at = time.monotonic()
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with self._agent.run_stream_events(
                    request.content,
                    deps=deps,
                    message_history=[],
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
                                event_task = asyncio.ensure_future(
                                    anext(event_iterator)
                                )
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
                    _log_usage(
                        events.usage,
                        run_id=request.run_id,
                        state=state,
                        messages=events.all_messages(),
                    )
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
        except UsageLimitExceeded as exc:
            if events is not None:
                _log_usage(
                    events.usage,
                    run_id=request.run_id,
                    state=state,
                    messages=events.all_messages(),
                )
            code = _usage_limit_failure_code(exc)
            logger.warning(
                "coach_usage_limit run_id=%s elapsed_ms=%s code=%s error=%s",
                request.run_id,
                round((time.monotonic() - started_at) * 1000),
                code,
                str(exc),
            )
            for activity in state.fail_running():
                yield ActivityChanged(activity)
            if thinking_active:
                yield ThinkingChanged(active=False)
            yield RunFailed(code=code, retryable=False)
            return
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
            yield RunFailed(
                code=_provider_failure_code(exc),
                retryable=_is_retryable_provider_error(exc),
            )
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


def _usage_limit_failure_code(error: UsageLimitExceeded) -> str:
    """Maps Pydantic AI's limit names to stable, public Coach error codes."""

    message = str(error).lower()
    if "per_request_input_tokens_limit" in message:
        return "context_limit"
    if "input_tokens_limit" in message:
        return "input_token_limit"
    if "output_tokens_limit" in message:
        return "output_token_limit"
    if "tool_calls_limit" in message:
        return "tool_call_limit"
    if "request_limit" in message:
        return "request_limit"
    if "cost_limit" in message:
        return "cost_limit"
    return "usage_limit"


def _provider_failure_code(error: Exception) -> str:
    """Classifies provider errors without exposing provider response details."""

    status_code = getattr(error, "status_code", None)
    message = str(error).lower()
    if status_code == 429 or "rate limit" in message:
        return "rate_limit"
    if (
        status_code in {401, 403}
        or "api key" in message
        or "authentication" in message
    ):
        return "provider_access"
    if status_code == 400 and ("context length" in message or "token" in message):
        return "context_limit"
    if status_code in {500, 502, 503, 504}:
        return "provider_unavailable"
    if "timeout" in message or "connection" in message:
        return "provider_unavailable"
    return "coach_run_failed"


def _is_retryable_provider_error(error: Exception) -> bool:
    """Returns whether repeating the same request may reasonably succeed."""

    return _provider_failure_code(error) not in {"provider_access", "context_limit"}


def create_pydantic_coach_runner() -> PydanticCoachRunner:
    """Build the explicit production runner from trusted Django settings."""

    return PydanticCoachRunner(
        model_name=str(settings.OPENAI_MODEL),
        timeout_seconds=float(settings.COACH_RUN_TIMEOUT_SECONDS),
        limits=CoachRuntimeLimits(
            recent_turns=int(settings.COACH_CONTEXT_RECENT_TURNS),
            context_token_reserve=int(settings.COACH_CONTEXT_TOKEN_RESERVE),
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


def _log_usage(
    usage: Any,
    *,
    run_id: Any,
    state: CoachRunState,
    messages: list[Any],
) -> None:
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
    record_token_usage(
        run_id=run_id,
        context_input_tokens=state.context_input_tokens,
        raw_turn_count=state.context_raw_turn_count,
        visible_turn_count=state.context_visible_turn_count,
        dropped_turn_count=state.context_dropped_turn_count,
        model_requests=_model_request_usage(messages, request_count=usage.requests),
        model_input_tokens=usage.input_tokens,
        model_output_tokens=usage.output_tokens,
        request_count=usage.requests,
        tool_call_count=usage.tool_calls,
        cost_usd=usage.cost,
    )


def _model_request_usage(
    messages: list[Any], *, request_count: int
) -> list[dict[str, object]]:
    """Return provider usage for this run's requests without recording content.

    The composed prompt can contain persisted raw history. Those old
    ``ModelResponse`` objects retain their original usage, so select only the
    final responses that belong to this run.
    """

    requests: list[dict[str, object]] = []
    responses = [message for message in messages if isinstance(message, ModelResponse)]
    for message in responses[-request_count:]:
        usage = message.usage
        requests.append(
            {
                "number": len(requests) + 1,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cached_tokens": usage.cache_read_tokens,
                "details": dict(usage.details),
            }
        )
    return requests
