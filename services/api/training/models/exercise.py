import uuid
from typing import TYPE_CHECKING, ClassVar

from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from .workout_exercise import WorkoutExercise


class Exercise(models.Model):
    class PrescriptionType(models.TextChoices):
        STRENGTH = "strength", "Strength"
        TIMED = "timed", "Timed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, blank=True, default="")
    name = models.CharField(max_length=200)
    prescription_type = models.CharField(
        max_length=32,
        choices=PrescriptionType.choices,
        default=PrescriptionType.STRENGTH,
    )
    default_sets = models.PositiveIntegerField(default=0)
    default_reps = models.PositiveIntegerField(default=0)
    default_weight = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True
    )
    default_weight_unit = models.CharField(max_length=16, default="lb")
    muscle_group = models.CharField(max_length=200, blank=True, default="")
    default_time = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    workout_exercises: "RelatedManager[WorkoutExercise]"

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return self.name
