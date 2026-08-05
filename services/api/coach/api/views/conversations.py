from __future__ import annotations

import uuid
from typing import Any, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from coach import services
from coach.api.serializers import (
    ConversationPageSerializer,
    ConversationPatchSerializer,
    ConversationSerializer,
    CursorQuerySerializer,
)


class ConversationCollectionAPIView(APIView):
    """Creates and lists the authenticated user's coach conversations."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ConversationSerializer

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_conversations_create",
        request=None,
        responses={201: ConversationSerializer},
    )
    def post(self, request: Request) -> Response:
        conversation = services.create_conversation(request.user)
        return Response(
            services.serialize_conversation(conversation),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_conversations_list",
        parameters=[CursorQuerySerializer],
        responses={200: ConversationPageSerializer},
    )
    def get(self, request: Request) -> Response:
        query = CursorQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        try:
            page = services.list_conversations(
                user=request.user,
                cursor=cast(dict[str, Any], query.validated_data).get("cursor"),
            )
        except services.InvalidCursor as exc:
            raise ValidationError({"cursor": str(exc)}) from exc
        return Response(
            {
                "next": page.next_cursor,
                "results": [
                    services.serialize_conversation_summary(item) for item in page.results
                ],
            }
        )


class ConversationDetailAPIView(APIView):
    """Retrieves, updates, or deletes one coach conversation."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ConversationSerializer

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_conversations_retrieve",
        responses={200: ConversationSerializer},
    )
    def get(self, request: Request, conversation_id: uuid.UUID) -> Response:
        return Response(
            services.serialize_conversation(
                _conversation_or_404(request, conversation_id)
            )
        )

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_conversations_patch",
        request=ConversationPatchSerializer,
        responses={200: ConversationSerializer},
    )
    def patch(self, request: Request, conversation_id: uuid.UUID) -> Response:
        serializer = ConversationPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = services.patch_conversation(
            user=request.user,
            conversation_id=conversation_id,
            updates=cast(dict[str, Any], serializer.validated_data),
        )
        return Response(services.serialize_conversation(conversation))

    @extend_schema(
        tags=["Coach"],
        operation_id="coach_conversations_delete",
        responses={204: OpenApiResponse(description="Conversation deleted.")},
    )
    def delete(self, request: Request, conversation_id: uuid.UUID) -> Response:
        try:
            services.delete_conversation(
                user=request.user, conversation_id=conversation_id
            )
        except services.CoachConversationNotFound as exc:
            raise NotFound(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


def _conversation_or_404(request: Request, conversation_id: uuid.UUID):
    """Gets the requested user-owned conversation or returns an API 404."""

    try:
        return services.get_conversation(
            user=request.user, conversation_id=conversation_id
        )
    except services.CoachConversationNotFound as exc:
        raise NotFound(str(exc)) from exc
