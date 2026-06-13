import uuid

from django.db import models


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

    class Meta:
        ordering = ["-date", "name"]

    def __str__(self) -> str:
        return self.name
