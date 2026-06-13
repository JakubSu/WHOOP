from rest_framework import serializers

from training.models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "name",
            "prescription_type",
            "default_sets",
            "default_reps",
            "muscle_group",
            "default_time",
            "notes",
        ]
        read_only_fields = ["id"]
