from decimal import Decimal
import uuid

from django.db import models


class Workout(models.Model):
    class Type(models.TextChoices):
        STRENGTH = "strength", "Strength"
        CONDITIONING = "conditioning", "Conditioning"
        CARDIO = "cardio", "Cardio"
        MOBILITY = "mobility", "Mobility"
        RECOVERY = "recovery", "Recovery"
        MIXED = "mixed", "Mixed"

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        RECOMMENDED_CHANGE_PENDING = (
            "recommended_change_pending",
            "Recommended change pending",
        )
        ACCEPTED = "accepted", "Accepted"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"
        MODIFIED = "modified", "Modified"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, blank=True, default="")
    training_plan = models.ForeignKey(
        "training.TrainingPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workouts",
    )
    scheduled_date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=200)
    workout_type = models.CharField(
        max_length=32, choices=Type.choices, default=Type.MIXED
    )
    status = models.CharField(
        max_length=64, choices=Status.choices, default=Status.PLANNED
    )
    planned_intensity = models.CharField(max_length=64, blank=True, default="")
    planned_duration_minutes = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_strain = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date", "name"]

    def __str__(self) -> str:
        return self.name
