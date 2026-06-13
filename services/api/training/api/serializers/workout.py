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
