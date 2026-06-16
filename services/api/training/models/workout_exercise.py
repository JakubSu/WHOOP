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
    sets = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField(default=0)
    time = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    weight_unit = models.CharField(max_length=16, default="lb")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    workout_id: uuid.UUID
    exercise_id: uuid.UUID

    class Meta:
        ordering = ["workout", "exercise__name"]

    def __str__(self) -> str:
        return f"{self.workout.name}: {self.exercise.name}"
