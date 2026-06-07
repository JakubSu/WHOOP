import uuid

from django.db import models


class Exercise(models.Model):
    class Category(models.TextChoices):
        STRENGTH = "strength", "Strength"
        CONDITIONING = "conditioning", "Conditioning"
        CARDIO = "cardio", "Cardio"
        MOBILITY = "mobility", "Mobility"
        RECOVERY = "recovery", "Recovery"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, blank=True, default="")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.STRENGTH)
    primary_muscle_group = models.CharField(max_length=200, blank=True, default="")
    secondary_muscle_groups = models.JSONField(default=list, blank=True)
    equipment = models.CharField(max_length=200, blank=True, default="")
    default_intensity = models.CharField(max_length=64, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    default_sets = models.PositiveIntegerField(default=0)
    default_reps = models.PositiveIntegerField(default=0)
    is_favorite = models.BooleanField(default=False)
    is_avoided = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
