from rest_framework import serializers

from training.models import TrainingPlan


class TrainingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPlan
        fields = [
            "id",
            "user_id",
            "name",
            "goal",
            "start_date",
            "end_date",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "created_at", "updated_at"]
