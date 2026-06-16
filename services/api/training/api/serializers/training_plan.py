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
        extra_kwargs = {
            "name": {"help_text": "Training plan name shown in the app."},
            "start_date": {"help_text": "Optional start date for the training plan."},
            "end_date": {"help_text": "Optional end date for the training plan."},
        }
