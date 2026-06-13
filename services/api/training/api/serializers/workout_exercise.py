from rest_framework import serializers

from training.models import WorkoutExercise


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutExercise
        fields = [
            "id",
            "workout",
            "exercise",
            "sets",
            "reps",
            "time",
            "weight",
            "weight_unit",
            "note",
        ]
        read_only_fields = ["id"]
