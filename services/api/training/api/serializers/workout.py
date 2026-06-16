from rest_framework import serializers

from training.models import Workout


class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            "id",
            "plan",
            "name",
            "date",
            "expected_time",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "plan": {"help_text": "Training plan identifier this workout belongs to."},
            "name": {"help_text": "Workout name shown in the training plan."},
            "date": {"help_text": "Optional scheduled date for the workout."},
            "expected_time": {"help_text": "Expected workout duration in minutes."},
        }
