from rest_framework import serializers

from training.models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "user_id",
            "name",
            "category",
            "primary_muscle_group",
            "equipment",
            "notes",
            "default_sets",
            "default_reps",
            "is_favorite",
            "is_avoided",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "created_at", "updated_at"]
