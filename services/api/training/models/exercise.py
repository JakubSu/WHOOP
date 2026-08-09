import uuid
from typing import TYPE_CHECKING, ClassVar

from django.db import models

if TYPE_CHECKING:
    from .workout_exercise import WorkoutExercise


MUSCLE_GROUP_VALUES = (
    "chest",
    "back",
    "shoulders",
    "biceps",
    "triceps",
    "forearms",
    "quads",
    "hamstrings",
    "glutes",
    "calves",
    "core",
    "full_body",
    "other",
)


class Exercise(models.Model):
    class PrescriptionType(models.TextChoices):
        STRENGTH = "strength", "Strength"
        TIMED = "timed", "Timed"

    class MuscleGroup(models.TextChoices):
        CHEST = "chest", "Chest"
        BACK = "back", "Back"
        SHOULDERS = "shoulders", "Shoulders"
        BICEPS = "biceps", "Biceps"
        TRICEPS = "triceps", "Triceps"
        FOREARMS = "forearms", "Forearms"
        QUADS = "quads", "Quads"
        HAMSTRINGS = "hamstrings", "Hamstrings"
        GLUTES = "glutes", "Glutes"
        CALVES = "calves", "Calves"
        CORE = "core", "Core"
        FULL_BODY = "full_body", "Full body"
        OTHER = "other", "Other"

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
    muscle_group = models.CharField(
        max_length=16,
        choices=MuscleGroup.choices,
        default=MuscleGroup.OTHER,
    )
    default_time = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    workout_exercises: models.Manager["WorkoutExercise"]

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(muscle_group__in=MUSCLE_GROUP_VALUES),
                name="exercise_muscle_group_valid",
            )
        ]

    def __str__(self) -> str:
        return self.name
