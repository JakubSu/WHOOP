from typing import ClassVar

from rest_framework import serializers

from training.models import Exercise, WorkoutExercise


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutExercise
        fields = (
            "id",
            "workout",
            "exercise",
            "sets",
            "reps",
            "time",
            "sort_order",
            "weight",
            "weight_unit",
            "note",
        )
        read_only_fields = ("id",)
        extra_kwargs: ClassVar[dict[str, dict[str, str]]] = {
            "workout": {"help_text": "Workout identifier this entry belongs to."},
            "exercise": {"help_text": "Exercise identifier referenced by this workout entry."},
            "sets": {"help_text": "Programmed set count for the workout exercise."},
            "reps": {"help_text": "Programmed repetition count for the workout exercise."},
            "time": {"help_text": "Programmed duration in seconds for timed exercises."},
            "sort_order": {"help_text": "Display order of the exercise inside the workout."},
            "weight": {"help_text": "Optional prescribed weight value."},
            "weight_unit": {"help_text": "Unit for the prescribed weight value."},
            "note": {"help_text": "Optional note specific to this workout exercise entry."},
        }


class WorkoutExerciseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutExercise
        fields = (
            "exercise",
            "sets",
            "reps",
            "time",
            "sort_order",
            "weight",
            "weight_unit",
            "note",
        )
        extra_kwargs: ClassVar[dict[str, dict[str, str]]] = {
            "exercise": {"help_text": "Exercise identifier referenced by this workout entry."},
            "sets": {"help_text": "Programmed set count for the workout exercise."},
            "reps": {"help_text": "Programmed repetition count for the workout exercise."},
            "time": {"help_text": "Programmed duration in seconds for timed exercises."},
            "sort_order": {"help_text": "Display order of the exercise inside the workout."},
            "weight": {"help_text": "Optional prescribed weight value."},
            "weight_unit": {"help_text": "Unit for the prescribed weight value."},
            "note": {"help_text": "Optional note specific to this workout exercise entry."},
        }


class WorkoutExerciseDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = (
            "id",
            "name",
            "muscle_group",
            "prescription_type",
        )
        read_only_fields = fields


class WorkoutExercisePageSerializer(serializers.ModelSerializer):
    exercise = WorkoutExerciseDisplaySerializer(read_only=True)

    class Meta:
        model = WorkoutExercise
        fields = (
            "id",
            "workout",
            "exercise",
            "sets",
            "reps",
            "time",
            "sort_order",
            "weight",
            "weight_unit",
            "note",
        )
        read_only_fields = fields
