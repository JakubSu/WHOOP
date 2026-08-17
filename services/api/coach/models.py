import uuid
from typing import TYPE_CHECKING, ClassVar

from django.conf import settings
from django.db import models

if TYPE_CHECKING:
    from recommendation.models import Recommendation


class CoachConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coach_conversations",
    )
    title = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    messages: models.Manager["CoachMessage"]

    class Meta:
        ordering: ClassVar[list[str]] = ["-updated_at", "-id"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["user", "updated_at"], name="coach_conv_user_updated_idx"
            )
        ]

    def __str__(self) -> str:
        return self.title or f"Coach conversation {self.id}"


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
    view_context = models.JSONField(null=True, blank=True)
    ai_message_batch = models.JSONField(null=True, blank=True)
    activity_log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    conversation_id: uuid.UUID
    # Reverse relation declared by Recommendation.coach_message.
    recommendations: models.Manager["Recommendation"]
    # Reverse relation declared by UiAction.message.
    ui_actions: models.Manager["UiAction"]

    class Meta:
        ordering: ClassVar[list[str]] = ["created_at", "id"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["conversation", "created_at", "id"],
                name="coach_msg_conv_created_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.role} message for {self.conversation_id}"


class UiAction(models.Model):
    """A durable, user-facing action requested by an assistant message."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        CoachMessage, on_delete=models.CASCADE, related_name="ui_actions"
    )
    type = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    payload = models.JSONField(default=dict)
    resolution = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["message", "status"], name="coach_uiaction_msg_status_idx")
        ]
