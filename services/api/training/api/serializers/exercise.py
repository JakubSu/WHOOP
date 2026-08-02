from typing import ClassVar

from rest_framework import serializers

from training.models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = (
            "id",
            "name",
            "prescription_type",
            "default_sets",
            "default_reps",
            "default_weight",
            "default_weight_unit",
            "muscle_group",
            "default_time",
            "notes",
        )
        read_only_fields = ("id",)
        extra_kwargs: ClassVar[dict[str, dict[str, str]]] = {
            "name": {"help_text": "Exercise name shown in the exercise library."},
            "prescription_type": {
                "help_text": "How the exercise is prescribed, for example strength or timed."
            },
            "default_sets": {"help_text": "Default set count for strength exercises."},
            "default_reps": {
                "help_text": "Default repetition count for strength exercises."
            },
            "default_weight": {
                "help_text": "Optional default prescribed weight for strength exercises."
            },
            "default_weight_unit": {
                "help_text": "Unit for the default prescribed weight value."
            },
            "muscle_group": {
                "help_text": "Primary muscle group associated with the exercise."
            },
            "default_time": {
                "help_text": "Default duration in seconds for timed exercises."
            },
            "notes": {
                "help_text": "Optional coaching notes or setup guidance for the exercise."
            },
        }


class ExerciseErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()
