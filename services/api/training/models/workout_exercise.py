from decimal import Decimal
import uuid

from django.db import models


class WorkoutExercise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workout = models.ForeignKey(
        "training.Workout", on_delete=models.CASCADE, related_name="workout_exercises"
    )
    exercise = models.ForeignKey(
        "training.Exercise", on_delete=models.PROTECT, related_name="workout_exercises"
    )
    position = models.PositiveIntegerField(default=1)
    sets = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    load = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    rest_seconds = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["workout", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["workout", "position"], name="unique_workout_exercise_position"
            )
        ]

    def __str__(self) -> str:
        return f"{self.workout.name} #{self.position}"
