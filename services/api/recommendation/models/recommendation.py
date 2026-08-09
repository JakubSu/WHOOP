import uuid
from typing import ClassVar

from django.conf import settings
from django.db import models
from django.db.models import Q


class Recommendation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        SUPERSEDED = "superseded", "Superseded"
        EXPIRED = "expired", "Expired"

    class Source(models.TextChoices):
        DAILY_RECOMMENDATION = "daily_recommendation", "Daily recommendation"
        COACH_CHAT = "coach_chat", "Coach chat"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    conversation = models.ForeignKey(
        "coaching.CoachConversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    coach_message = models.ForeignKey(
        "coaching.CoachMessage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    summary = models.CharField(max_length=500, blank=True, default="")
    reason = models.TextField(blank=True, default="")
    source = models.CharField(
        max_length=64,
        choices=Source.choices,
        default=Source.DAILY_RECOMMENDATION,
    )
    coach_card_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    expired_at = models.DateTimeField(null=True, blank=True)
    superseded_at = models.DateTimeField(null=True, blank=True)
    replaced_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaces",
    )
    run_id = models.UUIDField(null=True, blank=True, db_index=True)
    tool_call_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user_id: uuid.UUID
    conversation_id: uuid.UUID | None
    coach_message_id: uuid.UUID | None
    replaced_by_id: uuid.UUID | None
    operations: models.Manager["RecommendationOperation"]

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["user", "created_at"], name="rec_user_created_idx"),
            models.Index(
                fields=["conversation", "created_at"], name="rec_conversation_idx"
            ),
            models.Index(fields=["run_id", "status"], name="rec_run_status_idx"),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["run_id", "tool_call_id"],
                condition=Q(run_id__isnull=False, tool_call_id__isnull=False),
                name="rec_run_tool_call_unique",
            ),
            models.UniqueConstraint(
                fields=["conversation"],
                condition=Q(status="active", conversation__isnull=False),
                name="rec_one_active_per_conversation",
            ),
        ]


class RecommendationOperation(models.Model):
    class OperationType(models.TextChoices):
        ADD_WORKOUT = "add_workout", "Add workout"
        UPDATE_WORKOUT = "update_workout", "Update workout"
        REMOVE_WORKOUT = "remove_workout", "Remove workout"
        ADD_EXERCISE = "add_exercise", "Add exercise"
        UPDATE_EXERCISE = "update_exercise", "Update exercise"
        REMOVE_EXERCISE = "remove_exercise", "Remove exercise"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        STALE = "stale", "Stale"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.CASCADE, related_name="operations"
    )
    operation_type = models.CharField(max_length=32, choices=OperationType.choices)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    display_text = models.TextField(blank=True, default="")
    reason = models.TextField(blank=True, default="")
    payload = models.JSONField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    recommendation_id: uuid.UUID

    class Meta:
        ordering: ClassVar[list[str]] = ["created_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["recommendation", "status"], name="rec_op_pending_idx"
            ),
            models.Index(fields=["status", "created_at"], name="rec_op_status_idx"),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                condition=(
                    models.Q(status="pending", resolved_at__isnull=True)
                    | (
                        ~models.Q(status="pending")
                        & models.Q(resolved_at__isnull=False)
                    )
                ),
                name="rec_op_resolution_consistent",
            ),
        ]
