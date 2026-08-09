from __future__ import annotations

import json
import logging
import queue
import threading
import uuid
from collections.abc import Iterable, Iterator
from typing import Any, cast

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
    Keepalive,
    RunCompleted,
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
from coach.presentation import safe_activity_presentation

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
            {
                "next": page.next_cursor,
                "results": [services.serialize_message(item) for item in page.results],
            }
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
            result = get_coach_runner().run(run_request)
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
            user_content=content,
            result=result,
        )
        return Response(
            services.serialize_message(message), status=status.HTTP_201_CREATED
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

        def stream() -> Iterator[bytes]:
            sequence = 0
            thinking_active = False
            activities: dict[uuid.UUID, CoachActivity] = {}
            active_activity_ids: set[uuid.UUID] = set()
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
                runner_events = get_coach_runner().stream(run_request)
                for runner_event in _events_with_keepalive(
                    runner_events,
                    float(getattr(settings, "COACH_STREAM_KEEPALIVE_SECONDS", 15)),
                ):
                    if isinstance(runner_event, Keepalive):
                        yield b": keepalive\n\n"
                        continue
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
                        message = services.save_completed_turn(
                            user=request.user,
                            conversation=conversation,
                            user_message_id=user_message_id,
                            assistant_message_id=assistant_message_id,
                            user_content=content,
                            result=result,
                            activities=terminal_activities,
                        )
                        payload = services.serialize_message(message)
                        for operation in payload["operations"]:
                            yield event("operation", {"operation": operation})
                        yield event("completed", {"message": payload})
                        completed = True
                        break
                if not completed:
                    raise RuntimeError("Coach runner ended without a result.")
            except Exception:
                _expire_failed_run(request.user, run_request.run_id)
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

        return StreamingHttpResponse(stream(), content_type="text/event-stream")


def _run_request(request: Request, conversation: Any, content: str) -> CoachRunRequest:
    """Builds one runner request from the current conversation and user message."""

    return CoachRunRequest(
        run_id=uuid.uuid4(),
        conversation_id=conversation.id,
        user_id=request.user.id,
        content=content,
        ai_message_batches=services.load_ai_message_batches(conversation),
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
    )


def _merge_terminal_activities(
    streamed: Iterable[CoachActivity], final: Iterable[CoachActivity]
) -> list[CoachActivity]:
    """Combines streamed and final terminal activities by stable activity ID."""

    merged = {
        item.id: item
        for item in streamed
        if item.status in {"completed", "failed"}
    }
    merged.update(
        {
            item.id: item
            for item in final
            if item.status in {"completed", "failed"}
        }
    )
    return list(merged.values())


def _sse(name: str, data: dict[str, Any]) -> bytes:
    """Formats one owned event as a server-sent event frame."""

    return f"event: {name}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n".encode()


def _events_with_keepalive(
    events: Iterable[Any], interval_seconds: float = 15
) -> Iterator[Any]:
    """Yields runner events while inserting keepalives during idle periods."""

    event_queue: queue.Queue[Any] = queue.Queue(maxsize=100)
    cancelled = threading.Event()
    finished = object()

    def enqueue(item: Any) -> bool:
        while not cancelled.is_set():
            try:
                event_queue.put(item, timeout=0.1)
                return True
            except queue.Full:
                continue
        return False

    def consume() -> None:
        try:
            for item in events:
                if not enqueue(item):
                    return
        except Exception as exc:  # noqa: BLE001 - propagate runner failures to request thread.
            enqueue(exc)
        finally:
            enqueue(finished)

    threading.Thread(target=consume, daemon=True, name="coach-event-stream").start()
    try:
        while True:
            try:
                item = event_queue.get(timeout=interval_seconds)
            except queue.Empty:
                yield Keepalive()
                continue
            if item is finished:
                return
            if isinstance(item, Exception):
                raise item
            yield item
    finally:
        cancelled.set()
        close = getattr(events, "close", None)
        if callable(close):
            close()
