import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from .workout_exercise import WorkoutExercise


class Workout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, blank=True, default="")
    plan = models.ForeignKey(
        "training.TrainingPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workouts",
    )
    name = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    expected_time = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    plan_id: uuid.UUID | None
    workout_exercises: "RelatedManager[WorkoutExercise]"

    class Meta:
        ordering = ["-date", "name"]

    def __str__(self) -> str:
        return self.name
