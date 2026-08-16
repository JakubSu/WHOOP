"""Endpoints that resolve or dismiss durable coach UI actions."""

from __future__ import annotations

import uuid
from typing import Any, cast

from django.db import transaction
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from coach.api.serializers import CoachMessageSerializer
from coach.api.serializers.ui_actions import UiActionResolveSerializer
from coach.api.views.messages import EventStreamRenderer, MessageStreamAPIView
from coach.models import CoachMessage, UiAction
from training.models import Exercise


class UiActionDismissAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(
        self, request: Request, conversation_id: uuid.UUID, action_id: uuid.UUID
    ) -> Response:
        action = _pending_action_or_404(request, conversation_id, action_id)
        action.status = UiAction.Status.DISMISSED
        action.resolved_at = timezone.now()
        action.save(update_fields=["status", "resolved_at"])
        return Response(CoachMessageSerializer(action.message).data)


class UiActionResolveStreamAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (EventStreamRenderer,)

    @transaction.atomic
    def post(
        self, request: Request, conversation_id: uuid.UUID, action_id: uuid.UUID
    ) -> StreamingHttpResponse:
        serializer = UiActionResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = _pending_action_or_404(request, conversation_id, action_id)
        resolution_input = cast(dict[str, Any], serializer.validated_data)
        exercise_id = resolution_input["exercise_id"]

        try:
            exercise = Exercise.objects.get(
                id=exercise_id, user_id__in=[str(request.user.id), ""]
            )
        except Exercise.DoesNotExist as exc:
            raise NotFound("Exercise was not found.") from exc
        action.status = UiAction.Status.RESOLVED
        action.resolution = {
            "method": resolution_input["method"],
            "exercise_id": str(exercise.id),
        }
        action.resolved_at = timezone.now()
        action.save(update_fields=["status", "resolution", "resolved_at"])
        resolution_verb = (
            "creating" if resolution_input["method"] == "created" else "selecting"
        )
        visible_verb = "Created" if resolution_verb == "creating" else "Selected"
        content = (
            f"The user resolved UI action {action.id} by {resolution_verb} exercise {exercise.id}. "
            "Call get_exercise with that exact ID and continue the original recommendation request."
        )
        request._full_data = {"content": content}  # type: ignore[attr-defined]
        request._ui_action_visible_content = f"{visible_verb} {exercise.name}."  # type: ignore[attr-defined]
        # The continuation stream must replace the original assistant message in
        # the live chat. Otherwise its in-memory UI action remains "pending"
        # even though this transaction has resolved it.
        request._updated_message_ids = (action.message_id,)  # type: ignore[attr-defined]
        return MessageStreamAPIView().post(request, conversation_id)


def _pending_action_or_404(
    request: Request, conversation_id: uuid.UUID, action_id: uuid.UUID
) -> UiAction:
    try:
        return UiAction.objects.select_related("message__conversation").get(
            id=action_id,
            status=UiAction.Status.PENDING,
            message__role=CoachMessage.Role.ASSISTANT,
            message__conversation_id=conversation_id,
            message__conversation__user=request.user,
        )
    except UiAction.DoesNotExist as exc:
        raise NotFound("Pending UI action was not found.") from exc
