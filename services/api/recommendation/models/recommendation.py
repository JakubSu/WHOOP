import uuid
from typing import ClassVar

from django.conf import settings
from django.db import models


class Recommendation(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    conversation_id: uuid.UUID | None
    coach_message_id: uuid.UUID | None
    operations: models.Manager["RecommendationOperation"]

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["user", "created_at"], name="rec_user_created_idx"),
            models.Index(
                fields=["conversation", "created_at"], name="rec_conversation_idx"
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
        SUPERSEDED = "superseded", "Superseded"
        STALE = "stale", "Stale"

    class Source(models.TextChoices):
        DAILY_RECOMMENDATION = "daily_recommendation", "Daily recommendation"
        COACH_CHAT = "coach_chat", "Coach chat"

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
    source = models.CharField(
        max_length=64, choices=Source.choices, default=Source.DAILY_RECOMMENDATION
    )
    conversation = models.ForeignKey(
        "coaching.CoachConversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_operations",
    )
    message = models.ForeignKey(
        "coaching.CoachMessage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_operations",
    )
    supersedes = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(
        max_length=32,
        choices=[("user", "User"), ("coach_chat", "Coach chat"), ("system", "System")],
        default="coach_chat",
    )

    recommendation_id: uuid.UUID
    conversation_id: uuid.UUID | None
    message_id: uuid.UUID | None
    supersedes_id: uuid.UUID | None

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
            models.CheckConstraint(
                condition=~models.Q(id=models.F("supersedes_id")),
                name="rec_op_not_self_superseding",
            ),
        ]
