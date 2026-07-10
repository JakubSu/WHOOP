from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from coaching.models import CoachConversation, CoachMessage


class CoachConversationNotFound(ValueError):
    pass


class CoachValidationError(ValueError):
    pass


VALID_PAGE_TYPES = {choice.value for choice in CoachConversation.PageType}


def normalize_page_context(page_context: dict[str, Any]) -> dict[str, str]:
    page_type = str(page_context.get("page_type", "")).strip()
    if page_type not in VALID_PAGE_TYPES:
        raise CoachValidationError("Unsupported coach page type.")
    context_id = str(page_context.get("context_id") or "").strip()
    if page_type in {
        CoachConversation.PageType.WORKOUT,
        CoachConversation.PageType.TRAINING_PLAN,
    } and not context_id:
        raise CoachValidationError("Context id is required for this page type.")
    return {"page_type": page_type, "context_id": context_id}


@transaction.atomic
def get_or_create_active_conversation(
    *,
    user_id: str,
    page_context: dict[str, Any],
    conversation_id: str | None = None,
) -> CoachConversation:
    normalized = normalize_page_context(page_context)
    if conversation_id:
        try:
            conversation = CoachConversation.objects.select_for_update().get(
                pk=conversation_id,
                user_id=user_id,
                status=CoachConversation.Status.ACTIVE,
            )
        except CoachConversation.DoesNotExist as exc:
            raise CoachConversationNotFound("Coach conversation was not found.") from exc
        if (
            conversation.page_type != normalized["page_type"]
            or conversation.context_id != normalized["context_id"]
        ):
            raise CoachValidationError("Conversation does not match page context.")
        return conversation

    conversation, _ = CoachConversation.objects.select_for_update().get_or_create(
        user_id=user_id,
        page_type=normalized["page_type"],
        context_id=normalized["context_id"],
        status=CoachConversation.Status.ACTIVE,
    )
    return conversation


@transaction.atomic
def append_message(
    *,
    conversation: CoachConversation,
    role: str,
    content: str,
    metadata_json: dict[str, Any] | None = None,
    recommendation_id: str | None = None,
) -> CoachMessage:
    message = CoachMessage.objects.create(
        conversation=conversation,
        role=role,
        content=content,
        metadata_json=metadata_json or {},
        recommendation_id=recommendation_id,
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=["last_message_at", "updated_at"])
    return message


def list_conversation_messages(
    *,
    user_id: str,
    conversation_id: str,
) -> list[CoachMessage]:
    if not CoachConversation.objects.filter(pk=conversation_id, user_id=user_id).exists():
        raise CoachConversationNotFound("Coach conversation was not found.")
    return list(
        CoachMessage.objects.filter(conversation_id=conversation_id)
        .select_related("conversation")
        .order_by("created_at")
    )
