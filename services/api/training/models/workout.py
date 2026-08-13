import uuid
from typing import TYPE_CHECKING, ClassVar

from django.db import models

if TYPE_CHECKING:
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
    date = models.DateField()
    expected_time = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    plan_id: uuid.UUID | None
    workout_exercises: models.Manager["WorkoutExercise"]

    class Meta:
        ordering: ClassVar[list[str]] = ["date", "name"]

    def __str__(self) -> str:
        return self.name
