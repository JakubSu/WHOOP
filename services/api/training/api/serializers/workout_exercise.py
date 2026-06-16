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
        extra_kwargs = {
            "workout": {"help_text": "Workout identifier this entry belongs to."},
            "exercise": {"help_text": "Exercise identifier referenced by this workout entry."},
            "sets": {"help_text": "Programmed set count for the workout exercise."},
            "reps": {"help_text": "Programmed repetition count for the workout exercise."},
            "time": {"help_text": "Programmed duration in seconds for timed exercises."},
            "weight": {"help_text": "Optional prescribed weight value."},
            "weight_unit": {"help_text": "Unit for the prescribed weight value."},
            "note": {"help_text": "Optional note specific to this workout exercise entry."},
        }
