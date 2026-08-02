import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class CoachConversation(models.Model):
    class PageType(models.TextChoices):
        TODAY_WORKOUT = "today_workout", "Today workout"
        WORKOUT = "workout", "Workout"
        TRAINING_PLAN = "training_plan", "Training plan"
        RECOVERY = "recovery", "Recovery"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, db_index=True)
    page_type = models.CharField(max_length=32, choices=PageType.choices)
    context_id = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(blank=True, null=True)

    messages: "RelatedManager[CoachMessage]"

    class Meta:
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["user_id", "page_type", "context_id", "status"],
                name="coach_conv_scope_idx",
            ),
            models.Index(
                fields=["user_id", "last_message_at"],
                name="coach_conv_last_msg_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} {self.page_type} coach conversation"


class CoachMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        "coaching.CoachConversation",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    content = models.TextField()
    metadata_json = models.JSONField(default=dict)
    recommendation_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    conversation_id: uuid.UUID

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"],
                name="coach_msg_conversation_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.role} message for {self.conversation_id}"
