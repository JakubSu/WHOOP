from rest_framework import serializers


class WhoopConnectUrlSerializer(serializers.Serializer):
    connect_url = serializers.URLField(help_text="WHOOP OAuth authorization URL that the frontend should redirect the user to.")


class WhoopCallbackResultSerializer(serializers.Serializer):
    connected = serializers.BooleanField(help_text="Indicates that the WHOOP account was successfully connected.")


class WhoopSummarySerializer(serializers.Serializer):
    connected = serializers.BooleanField(help_text="Whether the current user has an active WHOOP connection.")
    detail = serializers.CharField(required=False, help_text="Human-readable detail when WHOOP is disconnected or unavailable.")
    snapshot_date = serializers.DateField(required=False, help_text="Date represented by the returned WHOOP summary snapshot.")
    recovery_score = serializers.FloatField(required=False, allow_null=True, help_text="WHOOP recovery score for the snapshot date.")
    sleep_performance_percent = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="WHOOP sleep performance percentage for the snapshot date.",
    )
    day_strain = serializers.FloatField(required=False, allow_null=True, help_text="WHOOP day strain value for the snapshot date.")
    hrv_rmssd_milli = serializers.FloatField(required=False, allow_null=True, help_text="Heart-rate variability in RMSSD milliseconds.")
    resting_heart_rate = serializers.FloatField(required=False, allow_null=True, help_text="Resting heart rate captured by WHOOP.")
    sleep_duration_minutes = serializers.IntegerField(required=False, allow_null=True, help_text="Sleep duration in whole minutes.")
    recent_workout_count = serializers.IntegerField(required=False, help_text="Count of recent workouts included in the summary rollup.")
    refreshed_at = serializers.DateTimeField(required=False, help_text="Timestamp when the WHOOP summary was last refreshed.")
