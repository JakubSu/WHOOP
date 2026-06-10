from rest_framework import serializers


class WorkoutSnapshotExerciseWriteSerializer(serializers.Serializer):
    workout_exercise_id = serializers.UUIDField(required=False, allow_null=True)
    snapshot_exercise_key = serializers.CharField(max_length=200)
    exercise = serializers.UUIDField()
    position = serializers.IntegerField(required=False, min_value=1)
    sets = serializers.IntegerField(required=False, min_value=0)
    reps = serializers.IntegerField(required=False, min_value=0)
    duration_seconds = serializers.IntegerField(required=False, min_value=0)
    distance = serializers.DecimalField(required=False, max_digits=8, decimal_places=2)
    load = serializers.DecimalField(required=False, max_digits=7, decimal_places=2)
    intensity = serializers.CharField(required=False, allow_blank=True, max_length=64)
    rest_seconds = serializers.IntegerField(required=False, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)


class WorkoutSnapshotWriteSerializer(serializers.Serializer):
    expected_version = serializers.CharField(required=False)
    training_plan = serializers.UUIDField(required=False, allow_null=True)
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    name = serializers.CharField(required=False, max_length=200)
    workout_type = serializers.CharField(required=False, max_length=32)
    status = serializers.CharField(required=False, max_length=64)
    planned_intensity = serializers.CharField(required=False, allow_blank=True, max_length=64)
    planned_duration_minutes = serializers.IntegerField(required=False, min_value=0)
    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    actual_strain = serializers.DecimalField(required=False, max_digits=5, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)
    exercises = WorkoutSnapshotExerciseWriteSerializer(required=False, many=True)
