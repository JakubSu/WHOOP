from rest_framework import serializers


class WhoopConnectUrlSerializer(serializers.Serializer):
    connect_url = serializers.URLField(
        help_text="WHOOP OAuth authorization URL that the frontend should redirect the user to."
    )


class WhoopAccessRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=("none", "pending", "approved", "rejected"), read_only=True
    )
    requested_at = serializers.DateTimeField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)


class WhoopCallbackResultSerializer(serializers.Serializer):
    connected = serializers.BooleanField(
        help_text="Indicates that the WHOOP account was successfully connected."
    )


class WhoopRecentWorkoutSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="WHOOP workout identifier.")
    sport_name = serializers.CharField(help_text="WHOOP sport name.")
    start = serializers.DateTimeField(help_text="Workout start timestamp.")
    end = serializers.DateTimeField(help_text="Workout end timestamp.")
    duration_minutes = serializers.IntegerField(
        help_text="Workout duration in whole minutes."
    )
    strain = serializers.FloatField(allow_null=True, help_text="Workout strain.")
    average_heart_rate = serializers.IntegerField(
        allow_null=True, help_text="Average workout heart rate."
    )
    max_heart_rate = serializers.IntegerField(
        allow_null=True, help_text="Max workout heart rate."
    )
    kilojoule = serializers.FloatField(
        allow_null=True, help_text="Workout energy in kilojoules."
    )
    distance_meter = serializers.FloatField(
        allow_null=True, help_text="Workout distance in meters."
    )
    score_state = serializers.CharField(help_text="WHOOP workout score state.")


class WhoopSummarySerializer(serializers.Serializer):
    connected = serializers.BooleanField(
        help_text="Whether the current user has an active WHOOP connection."
    )
    detail = serializers.CharField(
        required=False,
        help_text="Human-readable detail when WHOOP is disconnected or unavailable.",
    )
    snapshot_date = serializers.DateField(
        required=False,
        help_text="Date represented by the returned WHOOP summary snapshot.",
    )
    recovery_score = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="WHOOP recovery score for the snapshot date.",
    )
    sleep_performance_percent = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="WHOOP sleep performance percentage for the snapshot date.",
    )
    day_strain = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="WHOOP day strain value for the snapshot date.",
    )
    hrv_rmssd_milli = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Heart-rate variability in RMSSD milliseconds.",
    )
    resting_heart_rate = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Resting heart rate captured by WHOOP.",
    )
    sleep_duration_minutes = serializers.IntegerField(
        required=False, allow_null=True, help_text="Sleep duration in whole minutes."
    )
    recent_workout_count = serializers.IntegerField(
        required=False,
        help_text="Count of recent workouts included in the summary rollup.",
    )
    recent_workouts = WhoopRecentWorkoutSerializer(
        many=True,
        required=False,
        help_text="Summarized WHOOP workouts from the last 3 rolling days.",
    )
    refreshed_at = serializers.DateTimeField(
        required=False, help_text="Timestamp when the WHOOP summary was last refreshed."
    )
