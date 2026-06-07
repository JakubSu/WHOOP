from rest_framework import serializers

from training.models import WorkoutExercise


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutExercise
        fields = [
            "id",
            "workout",
            "exercise",
            "position",
            "sets",
            "reps",
            "duration_seconds",
            "distance",
            "load",
            "intensity",
            "rest_seconds",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
