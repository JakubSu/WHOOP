import uuid
from typing import ClassVar

from django.db import models


class Recommendation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPLIED = "applied", "Applied"
        REJECTED = "rejected", "Rejected"
        STALE = "stale", "Stale"
        FAILED = "failed", "Failed"

    class OperationType(models.TextChoices):
        ADD_EXERCISE = "add_exercise", "Add exercise"
        REMOVE_EXERCISE = "remove_exercise", "Remove exercise"
        REPLACE_EXERCISE = "replace_exercise", "Replace exercise"
        UPDATE_EXERCISE = "update_exercise", "Update exercise"
        MOVE_EXERCISE = "move_exercise", "Move exercise"
        ADD_WORKOUT = "add_workout", "Add workout"
        REMOVE_WORKOUT = "remove_workout", "Remove workout"
        UPDATE_WORKOUT = "update_workout", "Update workout"
        REVISE_WORKOUT = "revise_workout", "Revise workout"

    class Source(models.TextChoices):
        DAILY_RECOMMENDATION = "daily_recommendation", "Daily recommendation"
        COACH_CHAT = "coach_chat", "Coach chat"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, db_index=True)
    workout_id = models.UUIDField(db_index=True)
    snapshot_version = models.CharField(max_length=200)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
    )
    summary = models.TextField(blank=True, default="")
    reason = models.TextField(blank=True, default="")
    operation_type = models.CharField(
        max_length=64,
        choices=OperationType.choices,
        default=OperationType.UPDATE_EXERCISE,
    )
    payload_json = models.JSONField(default=dict)
    source = models.CharField(
        max_length=64,
        choices=Source.choices,
        default=Source.DAILY_RECOMMENDATION,
    )
    coach_conversation_id = models.UUIDField(blank=True, null=True, db_index=True)
    coach_message_id = models.UUIDField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["user_id", "workout_id"],
                name="recommendat_user_id_397991_idx",
            ),
            models.Index(
                fields=["user_id", "status"],
                name="recommendat_user_id_f8bf4c_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.workout_id} recommendation {self.status}"
