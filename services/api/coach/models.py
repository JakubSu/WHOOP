import uuid
from typing import TYPE_CHECKING, ClassVar

from django.conf import settings
from django.db import models

if TYPE_CHECKING:
    from recommendation.models import RecommendationOperation


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
            models.Index(fields=["user", "updated_at"], name="coach_conv_user_updated_idx")
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
    ai_message_batch = models.JSONField(null=True, blank=True)
    activity_log = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    conversation_id: uuid.UUID
    # Reverse relation declared by RecommendationOperation.message.
    recommendation_operations: models.Manager["RecommendationOperation"]

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
