from rest_framework import serializers

from training.models import TrainingPlan


class TrainingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPlan
        fields = [
            "id",
            "name",
            "start_date",
            "end_date",
        ]
        read_only_fields = ["id"]
