from rest_framework import serializers

from training.models import Workout


class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            "id",
            "user_id",
            "training_plan",
            "scheduled_date",
            "name",
            "workout_type",
            "status",
            "planned_intensity",
            "planned_duration_minutes",
            "completed_at",
            "actual_strain",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "created_at", "updated_at"]
