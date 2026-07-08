from rest_framework import serializers

from training.models import Exercise, WorkoutExercise


class PlanWorkoutSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    plan = serializers.UUIDField(source="plan_id", allow_null=True, read_only=True)
    name = serializers.CharField(read_only=True)
    date = serializers.DateField(allow_null=True, read_only=True)
    exercise_count = serializers.IntegerField(read_only=True)
    expected_time = serializers.IntegerField(read_only=True)


class WorkoutLandingWorkoutSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    plan = serializers.UUIDField(source="plan_id", allow_null=True, read_only=True)
    name = serializers.CharField(read_only=True)
    date = serializers.DateField(allow_null=True, read_only=True)
    expected_time = serializers.IntegerField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)


class WorkoutLandingSerializer(serializers.Serializer):
    has_workout_today = serializers.BooleanField(read_only=True)
    message = serializers.CharField(allow_null=True, read_only=True)
    selected_workout = WorkoutLandingWorkoutSerializer(allow_null=True, read_only=True)


class WorkoutExerciseDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = [
            "id",
            "name",
            "muscle_group",
            "prescription_type",
        ]
        read_only_fields = fields


class WorkoutExercisePageSerializer(serializers.ModelSerializer):
    exercise = WorkoutExerciseDisplaySerializer(read_only=True)

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
        read_only_fields = fields
