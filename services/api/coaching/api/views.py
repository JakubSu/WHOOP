from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from time import perf_counter
from typing import Any, cast

from django.http import StreamingHttpResponse
from rest_framework import permissions, status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ai.coach.events import sse_event
from ai.coach.orchestrator import CoachOrchestrator
from coaching import services
from coaching.api.serializers import (
    CoachConversationMessagesSerializer,
    CoachTurnStreamRequestSerializer,
)
from coaching.models import CoachMessage
from recommendation import services as recommendation_services


logger = logging.getLogger(__name__)


class EventStreamRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "event-stream"
    charset = "utf-8"

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict[str, Any] | None = None,
    ) -> bytes:
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return json.dumps(data, default=str).encode("utf-8")


class CoachTurnFailed(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "I could not complete that coach turn."
    default_code = "coach_turn_failed"


class CoachTurnStreamAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [EventStreamRenderer, JSONRenderer]
    serializer_class = CoachTurnStreamRequestSerializer

    def post(self, request: Request) -> StreamingHttpResponse:
        serializer = CoachTurnStreamRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        try:
            conversation = services.get_or_create_active_conversation(
                user_id=str(request.user.id),
                page_context=validated_data["page_context"],
                conversation_id=str(validated_data["conversation_id"])
                if validated_data.get("conversation_id")
                else None,
            )
        except services.CoachConversationNotFound as exc:
            raise NotFound(str(exc)) from exc
        except services.CoachValidationError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        logger.info(
            "coach_turn_conversation_ready user_id=%s conversation_id=%s page_type=%s context_id=%s message_length=%s",
            request.user.id,
            conversation.id,
            conversation.page_type,
            conversation.context_id,
            len(validated_data["message"]),
        )
        user_message = services.append_message(
            conversation=conversation,
            role=CoachMessage.Role.USER,
            content=validated_data["message"],
        )
        logger.info(
            "coach_turn_user_message_saved user_id=%s conversation_id=%s message_id=%s",
            request.user.id,
            conversation.id,
            user_message.id,
        )
        orchestrator = CoachOrchestrator()

        def stream() -> Iterator[bytes]:
            started_at = perf_counter()
            emitted_events = 0
            logger.info(
                "coach_turn_stream_started user_id=%s conversation_id=%s user_message_id=%s",
                request.user.id,
                conversation.id,
                user_message.id,
            )
            yield sse_event(
                "conversation_started",
                {
                    "conversation_id": str(conversation.id),
                    "page_context": {
                        "page_type": conversation.page_type,
                        "context_id": conversation.context_id,
                    },
                },
            ).encode("utf-8")
            emitted_events += 1
            logger.info(
                "coach_turn_stream_event_sent conversation_id=%s event=%s event_index=%s",
                conversation.id,
                "conversation_started",
                emitted_events,
            )
            try:
                result = orchestrator.run_turn(
                    user_id=str(request.user.id),
                    page_context={
                        "page_type": conversation.page_type,
                        "context_id": conversation.context_id,
                    },
                    message=user_message.content,
                    conversation_id=str(conversation.id),
                )
            except Exception:
                elapsed_ms = int((perf_counter() - started_at) * 1000)
                logger.exception(
                    "coach_turn_failed user_id=%s conversation_id=%s elapsed_ms=%s emitted_events=%s",
                    request.user.id,
                    conversation.id,
                    elapsed_ms,
                    emitted_events,
                )
                yield sse_event(
                    "error",
                    {
                        "code": "coach_turn_failed",
                        "message": "I could not complete that coach turn.",
                    },
                ).encode("utf-8")
                return

            for event in result.events:
                yield sse_event(event["event"], event["data"]).encode("utf-8")
                emitted_events += 1
                logger.info(
                    "coach_turn_stream_event_sent conversation_id=%s event=%s event_index=%s",
                    conversation.id,
                    event["event"],
                    emitted_events,
                )

            recommendation_id = (
                str(result.recommendation.id) if result.recommendation else None
            )
            logger.info(
                "coach_turn_assistant_message_saving user_id=%s conversation_id=%s answer_length=%s event_count=%s recommendation_id=%s",
                request.user.id,
                conversation.id,
                len(result.answer),
                len(result.events),
                recommendation_id,
            )
            assistant_message = services.append_message(
                conversation=conversation,
                role=CoachMessage.Role.ASSISTANT,
                content=result.answer,
                metadata_json={
                    "safety_flags": result.safety_flags,
                    "ui_actions": result.ui_actions,
                },
                recommendation_id=recommendation_id,
            )
            logger.info(
                "coach_turn_assistant_message_saved user_id=%s conversation_id=%s message_id=%s safety_flags=%s ui_actions=%s",
                request.user.id,
                conversation.id,
                assistant_message.id,
                ",".join(result.safety_flags) if result.safety_flags else "none",
                len(result.ui_actions),
            )
            if result.recommendation:
                result.recommendation.coach_message_id = assistant_message.id
                result.recommendation.save(
                    update_fields=["coach_message_id", "updated_at"]
                )
                logger.info(
                    "coach_turn_recommendation_linked conversation_id=%s recommendation_id=%s assistant_message_id=%s",
                    conversation.id,
                    result.recommendation.id,
                    assistant_message.id,
                )
                yield sse_event(
                    "recommendation_created",
                    {
                        "recommendation": recommendation_services.serialize_recommendation(
                            result.recommendation
                        )
                    },
                ).encode("utf-8")
                emitted_events += 1
                logger.info(
                    "coach_turn_stream_event_sent conversation_id=%s event=%s event_index=%s",
                    conversation.id,
                    "recommendation_created",
                    emitted_events,
                )
            yield sse_event(
                "assistant_done",
                {
                    "message": {
                        "id": str(assistant_message.id),
                        "role": assistant_message.role,
                        "content": assistant_message.content,
                    }
                },
            ).encode("utf-8")
            emitted_events += 1
            elapsed_ms = int((perf_counter() - started_at) * 1000)
            logger.info(
                "coach_turn_stream_completed user_id=%s conversation_id=%s assistant_message_id=%s elapsed_ms=%s emitted_events=%s",
                request.user.id,
                conversation.id,
                assistant_message.id,
                elapsed_ms,
                emitted_events,
            )

        return StreamingHttpResponse(stream(), content_type="text/event-stream")


class CoachConversationMessagesAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoachConversationMessagesSerializer

    def get(self, request: Request, conversation_id: str) -> Response:
        try:
            messages = services.list_conversation_messages(
                user_id=str(request.user.id),
                conversation_id=str(conversation_id),
            )
        except services.CoachConversationNotFound as exc:
            raise NotFound(str(exc)) from exc
        return Response(
            {
                "conversation_id": str(conversation_id),
                "messages": [
                    {
                        "id": str(message.id),
                        "role": message.role,
                        "content": message.content,
                        "metadata_json": message.metadata_json,
                        "recommendation_id": str(message.recommendation_id)
                        if message.recommendation_id
                        else None,
                        "created_at": message.created_at.isoformat(),
                    }
                    for message in messages
                ],
            }
        )
