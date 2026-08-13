import uuid
from typing import TYPE_CHECKING, ClassVar

from django.db import models
from django.db.models import Q

if TYPE_CHECKING:
    from .workout import Workout


class TrainingPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=200, blank=True, default="")
    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    workouts: models.Manager["Workout"]

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at", "name"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["user_id"],
                condition=~Q(user_id=""),
                name="training_plan_one_per_user",
            ),
        ]

    def __str__(self) -> str:
        return self.name
