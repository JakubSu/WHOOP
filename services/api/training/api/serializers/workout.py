from typing import ClassVar

from rest_framework import serializers

from training.models import Workout


class WorkoutSerializer(serializers.ModelSerializer):
    exercise_count = serializers.SerializerMethodField()

    class Meta:
        model = Workout
        fields = (
            "id",
            "name",
            "date",
            "expected_time",
            "exercise_count",
        )
        read_only_fields = ("id", "exercise_count")
        extra_kwargs: ClassVar[dict[str, dict[str, str]]] = {
            "name": {"help_text": "Workout name shown in the training plan."},
            "date": {"help_text": "Scheduled date for the workout."},
            "expected_time": {"help_text": "Expected workout duration in minutes."},
        }

    def get_exercise_count(self, obj: Workout) -> int:
        annotated_count = getattr(obj, "exercise_count", None)
        if annotated_count is not None:
            return int(annotated_count)
        return obj.workout_exercises.count()


class WorkoutErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class WorkoutLandingQuerySerializer(serializers.Serializer):
    today = serializers.DateField()


class WorkoutLandingWorkoutSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    plan = serializers.UUIDField(source="plan_id", allow_null=True, read_only=True)
    name = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True)
    expected_time = serializers.IntegerField(read_only=True)
    is_today = serializers.BooleanField(read_only=True)


class WorkoutLandingSerializer(serializers.Serializer):
    has_workout_today = serializers.BooleanField(read_only=True)
    message = serializers.CharField(allow_null=True, read_only=True)
    selected_workout = WorkoutLandingWorkoutSerializer(allow_null=True, read_only=True)
