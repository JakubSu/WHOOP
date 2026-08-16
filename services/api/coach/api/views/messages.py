from __future__ import annotations

import asyncio
import inspect
import json
import logging
import uuid
from collections.abc import AsyncIterable, AsyncIterator, Iterable
from contextlib import suppress
from typing import Any, cast

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.http import StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.runner import (
    ActivityChanged,
    CoachActivity,
    CoachRunnerUnavailable,
    CoachRunRequest,
    CoachRunResult,
    RunCompleted,
    RunFailed,
    TextDelta,
    ThinkingChanged,
    get_coach_runner,
)
from coach import services
from coach.api.serializers import (
    CoachMessageSerializer,
    CursorQuerySerializer,
    MessageCreateSerializer,
    MessagePageSerializer,
)
from coach.api.views.conversations import _conversation_or_404
from coach.presentation import (
    recommendation_transitions_for_message,
    safe_activity_presentation,
    updated_messages_for_message,
)

logger = logging.getLogger(__name__)


class EventStreamRenderer(BaseRenderer):
    """Renders the owned Coach server-sent event stream."""

    media_type = "text/event-stream"
    format = "event-stream"
    charset = "utf-8"

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        return b"" if data is None else str(data).encode("utf-8")


class CoachUnavailable(APIException):
    """Reports that no coach runner is available to serve a request."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The coach is temporarily unavailable."
    default_code = "coach_unavailable"


class MessageCollectionAPIView(APIView):
    """Lists messages or runs a complete non-streaming coach turn."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CoachMessageSerializer

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_messages_list",
        parameters=[CursorQuerySerializer],
        responses={200: MessagePageSerializer},
    )
    def get(self, request: Request, conversation_id: uuid.UUID) -> Response:
        query = CursorQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        try:
            page = services.list_messages(
                user=request.user,
                conversation_id=conversation_id,
                cursor=cast(dict[str, Any], query.validated_data).get("cursor"),
            )
        except services.CoachConversationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.InvalidCursor as exc:
            raise ValidationError({"cursor": str(exc)}) from exc
        return Response(
            MessagePageSerializer(
                {"next": page.next_cursor, "results": page.results}
            ).data
        )

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_messages_create",
        request=MessageCreateSerializer,
        responses={201: CoachMessageSerializer},
    )
    def post(self, request: Request, conversation_id: uuid.UUID) -> Response:
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = _conversation_or_404(request, conversation_id)
        content = cast(dict[str, Any], serializer.validated_data)["content"]
        run_request = _run_request(request, conversation, content)
        try:
            runner = get_coach_runner()
            result = async_to_sync(runner.run)(run_request)
        except CoachRunnerUnavailable as exc:
            raise CoachUnavailable() from exc
        except Exception as exc:
            _expire_failed_run(request.user, run_request.run_id)
            logger.exception("coach_run_failed run_id=%s", run_request.run_id)
            raise CoachUnavailable() from exc
        result = _sanitize_result(result)
        message = services.save_completed_turn(
            user=request.user,
            conversation=conversation,
            user_message_id=uuid.uuid4(),
            assistant_message_id=uuid.uuid4(),
            user_content=run_request.visible_content or content,
            result=result,
        )
        try:
            async_to_sync(runner.maintain_memory)(
                conversation_id=conversation.id, user_id=request.user.id
            )
        except Exception:  # noqa: BLE001 - memory cannot invalidate a saved turn
            logger.exception(
                "coach_memory_maintenance_failed conversation_id=%s", conversation.id
            )
        return Response(
            CoachMessageSerializer(message).data, status=status.HTTP_201_CREATED
        )


class MessageStreamAPIView(APIView):
    """Streams a coach turn using the owned version-one SSE contract."""

    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (EventStreamRenderer, JSONRenderer)
    serializer_class = MessageCreateSerializer

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_messages_stream",
        request=MessageCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="Owned Coach SSE v1 event stream.",
            )
        },
    )
    def post(
        self, request: Request, conversation_id: uuid.UUID
    ) -> StreamingHttpResponse:
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = _conversation_or_404(request, conversation_id)
        content = cast(dict[str, Any], serializer.validated_data)["content"]
        run_request = _run_request(request, conversation, content)
        assistant_message_id = uuid.uuid4()
        user_message_id = uuid.uuid4()

        async def stream() -> AsyncIterator[bytes]:
            sequence = 0
            thinking_active = False
            activities: dict[str, CoachActivity] = {}
            active_activity_ids: set[str] = set()
            completed = False

            def event(name: str, payload: dict[str, Any] | None = None) -> bytes:
                nonlocal sequence
                data = {
                    "version": 1,
                    "sequence": sequence,
                    "run_id": str(run_request.run_id),
                    "conversation_id": str(conversation.id),
                    "message_id": str(assistant_message_id),
                    **(payload or {}),
                }
                sequence += 1
                return _sse(name, data)

            yield event("message_started")
            yield event("thinking_started", {"label": "Thinking…"})
            thinking_active = True
            try:
                runner = get_coach_runner()
                runner_events = runner.stream(run_request)
                async for runner_event in runner_events:
                    if isinstance(runner_event, ThinkingChanged):
                        if runner_event.active and not thinking_active:
                            yield event("thinking_started", {"label": "Thinking…"})
                            thinking_active = True
                        elif not runner_event.active and thinking_active:
                            yield event("thinking_finished")
                            thinking_active = False
                        continue
                    if isinstance(runner_event, TextDelta):
                        if thinking_active:
                            yield event("thinking_finished")
                            thinking_active = False
                        if runner_event.delta:
                            yield event("text_delta", {"delta": runner_event.delta})
                        continue
                    if isinstance(runner_event, ActivityChanged):
                        if thinking_active:
                            yield event("thinking_finished")
                            thinking_active = False
                        activity = _sanitize_activity(runner_event.activity)
                        activities[activity.id] = activity
                        if activity.status == "running":
                            active_activity_ids.add(activity.id)
                        else:
                            active_activity_ids.discard(activity.id)
                        event_name = {
                            "running": "tool_started",
                            "completed": "tool_completed",
                            "failed": "tool_failed",
                        }[activity.status]
                        yield event(event_name, {"activity": activity.as_dict()})
                        if activity.status == "completed" and not active_activity_ids:
                            yield event("thinking_started", {"label": "Thinking…"})
                            thinking_active = True
                        continue
                    if isinstance(runner_event, RunCompleted):
                        yield event("thinking_finished")
                        thinking_active = False
                        result = _sanitize_result(runner_event.result)
                        terminal_activities = _merge_terminal_activities(
                            activities.values(), result.activities
                        )
                        message = await sync_to_async(
                            services.save_completed_turn, thread_sensitive=True
                        )(
                            user=request.user,
                            conversation=conversation,
                            user_message_id=user_message_id,
                            assistant_message_id=assistant_message_id,
                            user_content=run_request.visible_content or content,
                            result=result,
                            activities=terminal_activities,
                        )
                        try:
                            await runner.maintain_memory(
                                conversation_id=conversation.id, user_id=request.user.id
                            )
                        except Exception:  # noqa: BLE001 - memory cannot invalidate a saved turn
                            logger.exception(
                                "coach_memory_maintenance_failed conversation_id=%s",
                                conversation.id,
                            )
                        payload, transitions, updated_messages = await sync_to_async(
                            _completed_message_payload, thread_sensitive=True
                        )(
                            message,
                            updated_message_ids=getattr(
                                request, "_updated_message_ids", ()
                            ),
                        )
                        yield event(
                            "completed",
                            {
                                "message": payload,
                                "recommendation_transitions": transitions,
                                "updated_messages": updated_messages,
                            },
                        )
                        completed = True
                        break
                    if isinstance(runner_event, RunFailed):
                        await sync_to_async(_expire_failed_run, thread_sensitive=True)(
                            request.user, run_request.run_id
                        )
                        if thinking_active:
                            yield event("thinking_finished")
                        yield event(
                            "error",
                            {
                                "code": runner_event.code,
                                "message": "I couldn't complete that request.",
                                "retryable": runner_event.retryable,
                            },
                        )
                        completed = True
                        break
                if not completed:
                    raise RuntimeError("Coach runner ended without a result.")
            except asyncio.CancelledError:
                logger.info("coach_stream_cancelled run_id=%s", run_request.run_id)
                raise
            except Exception:
                await sync_to_async(_expire_failed_run, thread_sensitive=True)(
                    request.user, run_request.run_id
                )
                yield event("thinking_finished")
                logger.exception("coach_stream_failed run_id=%s", run_request.run_id)
                yield event(
                    "error",
                    {
                        "code": "coach_run_failed",
                        "message": "I couldn’t complete that request.",
                        "retryable": True,
                    },
                )

        response = StreamingHttpResponse(
            _with_sse_heartbeats(
                stream(),
                interval_seconds=float(
                    getattr(settings, "COACH_STREAM_KEEPALIVE_SECONDS", 15)
                ),
            ),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response


def _run_request(request: Request, conversation: Any, content: str) -> CoachRunRequest:
    """Builds one runner request from the current conversation and user message."""

    return CoachRunRequest(
        run_id=uuid.uuid4(),
        conversation_id=conversation.id,
        user_id=request.user.id,
        content=content,
        ai_message_batches=services.load_ai_message_batches(conversation),
        visible_content=getattr(request, "_ui_action_visible_content", None),
    )


def _expire_failed_run(user: Any, run_id: uuid.UUID) -> None:
    """Expires recommendation ledgers created before an unsuccessful coach run."""

    from recommendation.services import expire_run_recommendations

    try:
        expire_run_recommendations(user=user, run_id=run_id)
    except Exception:
        logger.exception("coach_run_expiry_failed run_id=%s", run_id)


def _sanitize_activity(activity: CoachActivity) -> CoachActivity:
    """Maps a runner activity to a safe public presentation."""

    kind, label = safe_activity_presentation(activity.kind)
    return CoachActivity(id=activity.id, kind=kind, label=label, status=activity.status)


def _sanitize_result(result: CoachRunResult) -> CoachRunResult:
    """Removes non-terminal or unsafe activity details from a completed run."""

    return CoachRunResult(
        content=result.content,
        ai_message_batch=result.ai_message_batch,
        activities=[
            _sanitize_activity(item)
            for item in result.activities
            if item.status in {"completed", "failed"}
        ],
        recommendation_id=result.recommendation_id,
        ui_actions=result.ui_actions,
    )


def _merge_terminal_activities(
    streamed: Iterable[CoachActivity], final: Iterable[CoachActivity]
) -> list[CoachActivity]:
    """Combines streamed and final terminal activities by stable activity ID."""

    merged = {
        item.id: item for item in streamed if item.status in {"completed", "failed"}
    }
    merged.update(
        {item.id: item for item in final if item.status in {"completed", "failed"}}
    )
    return list(merged.values())


def _sse(name: str, data: dict[str, Any]) -> bytes:
    """Formats one owned event as a server-sent event frame."""

    return (
        f"event: {name}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n".encode()
    )


async def _with_sse_heartbeats(
    frames: AsyncIterable[bytes], interval_seconds: float = 15
) -> AsyncIterator[bytes]:
    """Yields SSE frames and comments while preserving an idle connection."""

    iterator = aiter(frames)
    pending = asyncio.ensure_future(anext(iterator))
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=interval_seconds)
            if not done:
                yield b": keepalive\n\n"
                continue
            try:
                item = pending.result()
            except StopAsyncIteration:
                return
            pending = asyncio.ensure_future(anext(iterator))
            yield item
    finally:
        pending.cancel()
        with suppress(asyncio.CancelledError, StopAsyncIteration):
            await pending
        close = getattr(iterator, "aclose", None)
        if callable(close):
            close_result = close()
            if inspect.isawaitable(close_result):
                await close_result


def _completed_message_payload(
    message: Any, *, updated_message_ids: Iterable[Any] = ()
) -> tuple[dict[str, Any], Any, list[Any]]:
    """Builds DB-backed completed-event fields outside the async event loop."""

    return (
        cast(dict[str, Any], CoachMessageSerializer(message).data),
        recommendation_transitions_for_message(message),
        cast(
            list[Any],
            CoachMessageSerializer(
                updated_messages_for_message(
                    message, additional_message_ids=updated_message_ids
                ),
                many=True,
            ).data,
        ),
    )
