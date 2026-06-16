import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from .recommendation import Recommendation, RecommendationOperation


class Recommendation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        PARTIAL = "partial", "Partial"
        STALE = "stale", "Stale"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, db_index=True)
    workout_id = models.UUIDField(db_index=True)
    snapshot_version = models.CharField(max_length=200)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
    )
    summary = models.TextField(blank=True, default="")
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    operations: "RelatedManager[RecommendationOperation]"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
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


class RecommendationOperation(models.Model):
    class Type(models.TextChoices):
        REPLACE_EXERCISE = "replace_exercise", "Replace exercise"
        UPDATE_EXERCISE = "update_exercise", "Update exercise"
        REMOVE_EXERCISE = "remove_exercise", "Remove exercise"
        ADD_EXERCISE = "add_exercise", "Add exercise"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        STALE = "stale", "Stale"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(
        "recommendation.Recommendation",
        on_delete=models.CASCADE,
        related_name="operations",
    )
    sequence = models.PositiveIntegerField()
    operation_type = models.CharField(max_length=64, choices=Type.choices)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING
    )
    payload_json = models.JSONField(default=dict)
    decided_at = models.DateTimeField(blank=True, null=True)
    applied_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    recommendation_id: uuid.UUID

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["recommendation", "sequence"],
                name="unique_recommendation_operation_sequence",
            )
        ]

    def __str__(self) -> str:
        return f"{self.id} #{self.sequence} {self.operation_type}"
