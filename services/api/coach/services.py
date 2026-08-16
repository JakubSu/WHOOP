from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Q, Subquery
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ai.runner import CoachActivity, CoachRunResult
from coach.models import CoachConversation, CoachMessage, UiAction

CONVERSATION_PAGE_SIZE = 20
MESSAGE_PAGE_SIZE = 30


class CoachConversationNotFound(ValueError):
    """Indicates that a coach conversation is missing or belongs to another user."""


class InvalidCursor(ValueError):
    """Indicates that a supplied opaque pagination cursor cannot be decoded."""


@dataclass(frozen=True)
class Page:
    """Represents one cursor-paginated result page."""

    results: list[Any]
    next_cursor: str | None


def create_conversation(user: Any) -> CoachConversation:
    """Creates a new empty coach conversation for the authenticated user."""

    return CoachConversation.objects.create(user=user)


def get_conversation(*, user: Any, conversation_id: uuid.UUID) -> CoachConversation:
    """Gets a user-owned conversation or raises a not-found domain error."""

    try:
        return CoachConversation.objects.get(pk=conversation_id, user=user)
    except CoachConversation.DoesNotExist as exc:
        raise CoachConversationNotFound("Coach conversation was not found.") from exc


def list_conversations(*, user: Any, cursor: str | None = None) -> Page:
    """Lists the user's conversations in newest-first cursor order."""

    latest_content = (
        CoachMessage.objects.filter(conversation_id=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("content")[:1]
    )
    queryset = CoachConversation.objects.filter(user=user).annotate(
        last_message_preview=Subquery(latest_content)
    )
    if cursor:
        cursor_time, cursor_id = _decode_cursor(cursor)
        queryset = queryset.filter(
            Q(updated_at__lt=cursor_time) | Q(updated_at=cursor_time, id__lt=cursor_id)
        )
    rows = list(queryset.order_by("-updated_at", "-id")[: CONVERSATION_PAGE_SIZE + 1])
    has_more = len(rows) > CONVERSATION_PAGE_SIZE
    rows = rows[:CONVERSATION_PAGE_SIZE]
    next_cursor = _encode_cursor(rows[-1].updated_at, rows[-1].id) if has_more else None
    return Page(rows, next_cursor)


def patch_conversation(
    *, user: Any, conversation_id: uuid.UUID, updates: dict[str, Any]
) -> CoachConversation:
    """Applies supported updates to one user-owned coach conversation."""

    conversation = get_conversation(user=user, conversation_id=conversation_id)
    update_fields: list[str] = []
    if "title" in updates:
        conversation.title = updates["title"].strip()
        update_fields.append("title")
    conversation.save(update_fields=[*update_fields, "updated_at"])
    return conversation


@transaction.atomic
def delete_conversation(*, user: Any, conversation_id: uuid.UUID) -> None:
    """Deletes chat history while staling its unresolved recommendation operations."""

    from recommendation.models import Recommendation, RecommendationOperation
    from recommendation.services.presentation import refresh_coach_card_snapshot

    conversation = get_conversation(user=user, conversation_id=conversation_id)
    now = timezone.now()
    RecommendationOperation.objects.filter(
        recommendation__conversation=conversation,
        status=RecommendationOperation.Status.PENDING,
    ).update(
        status=RecommendationOperation.Status.STALE,
        resolved_at=now,
        updated_at=now,
    )
    for recommendation in Recommendation.objects.filter(conversation=conversation):
        if not recommendation.operations.filter(
            status=RecommendationOperation.Status.PENDING
        ).exists():
            recommendation.status = Recommendation.Status.COMPLETED
            recommendation.save(update_fields=["status", "updated_at"])
        refresh_coach_card_snapshot(recommendation)
    conversation.delete()


def list_messages(
    *, user: Any, conversation_id: uuid.UUID, cursor: str | None = None
) -> Page:
    """Lists a conversation's messages in chronological display order."""

    conversation = get_conversation(user=user, conversation_id=conversation_id)
    queryset = CoachMessage.objects.filter(conversation=conversation).prefetch_related(
        _recommendation_card_prefetch(), "ui_actions"
    )
    if cursor:
        cursor_time, cursor_id = _decode_cursor(cursor)
        queryset = queryset.filter(
            Q(created_at__lt=cursor_time) | Q(created_at=cursor_time, id__lt=cursor_id)
        )
    rows = list(queryset.order_by("-created_at", "-id")[: MESSAGE_PAGE_SIZE + 1])
    has_more = len(rows) > MESSAGE_PAGE_SIZE
    rows = rows[:MESSAGE_PAGE_SIZE]
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    rows.reverse()
    return Page(rows, next_cursor)


def load_ai_message_batches(
    conversation: CoachConversation,
) -> list[list[dict[str, Any]]]:
    """Loads completed assistant batches for reconstruction of private model history."""

    return list(
        CoachMessage.objects.filter(
            conversation=conversation,
            role=CoachMessage.Role.ASSISTANT,
            ai_message_batch__isnull=False,
        )
        .order_by("created_at", "id")
        .values_list("ai_message_batch", flat=True)
    )


@transaction.atomic
def save_completed_turn(
    *,
    user: Any,
    conversation: CoachConversation,
    user_message_id: uuid.UUID,
    assistant_message_id: uuid.UUID,
    user_content: str,
    result: CoachRunResult,
    activities: list[CoachActivity] | None = None,
) -> CoachMessage:
    """Atomically persists a completed user turn and its assistant response."""

    CoachMessage.objects.create(
        id=user_message_id,
        conversation=conversation,
        role=CoachMessage.Role.USER,
        content=user_content,
    )
    assistant_message = CoachMessage.objects.create(
        id=assistant_message_id,
        conversation=conversation,
        role=CoachMessage.Role.ASSISTANT,
        content=result.content,
        ai_message_batch=result.ai_message_batch,
        activity_log=[item.as_dict() for item in (activities or result.activities)],
    )
    UiAction.objects.bulk_create(
        [
            UiAction(
                message=assistant_message,
                type=action.type,
                payload=action.payload.model_dump(mode="json"),
            )
            for action in result.ui_actions
        ]
    )
    if result.recommendation_id is not None:
        from recommendation.services import attach_recommendation_to_coach_message

        attach_recommendation_to_coach_message(
            user=user,
            conversation=conversation,
            coach_message=assistant_message,
            recommendation_id=result.recommendation_id,
        )
    conversation.save(update_fields=["updated_at"])
    return (
        CoachMessage.objects.filter(pk=assistant_message.pk)
        .prefetch_related(_recommendation_card_prefetch(), "ui_actions")
        .get()
    )


def _recommendation_card_prefetch() -> Prefetch:
    """Loads each persisted chat card and its derived actionability flag."""

    from recommendation.models import Recommendation, RecommendationOperation

    pending_operations = RecommendationOperation.objects.filter(
        recommendation_id=OuterRef("pk"),
        status=RecommendationOperation.Status.PENDING,
    )
    return Prefetch(
        "recommendations",
        queryset=Recommendation.objects.annotate(
            has_pending_operations=Exists(pending_operations)
        ),
        to_attr="coach_card_recommendations",
    )


def _encode_cursor(timestamp: datetime, row_id: uuid.UUID) -> str:
    """Encodes a timestamp and row identifier as an opaque cursor."""

    raw = json.dumps([timestamp.isoformat(), str(row_id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decodes an opaque cursor or raises InvalidCursor."""

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw_time, raw_id = json.loads(base64.urlsafe_b64decode(padded).decode())
        parsed_time = parse_datetime(raw_time)
        if parsed_time is None:
            raise ValueError
        return parsed_time, uuid.UUID(raw_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidCursor("Cursor is invalid.") from exc
