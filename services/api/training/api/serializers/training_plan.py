from typing import ClassVar

from rest_framework import serializers

from training.models import TrainingPlan


class TrainingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPlan
        fields = (
            "id",
            "name",
            "start_date",
            "end_date",
        )
        read_only_fields = ("id",)
        extra_kwargs: ClassVar[dict[str, dict[str, str]]] = {
            "name": {"help_text": "Training plan name shown in the app."},
            "start_date": {"help_text": "Optional start date for the training plan."},
            "end_date": {"help_text": "Optional end date for the training plan."},
        }


class PlanWorkoutSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    plan = serializers.UUIDField(source="plan_id", allow_null=True, read_only=True)
    name = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True)
    exercise_count = serializers.IntegerField(read_only=True)
    expected_time = serializers.IntegerField(read_only=True)
