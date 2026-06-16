from rest_framework import serializers


class ApproveRecommendationSerializer(serializers.Serializer):
    expected_workout_version = serializers.CharField(
        required=False,
        allow_blank=False,
        help_text="Optional workout version the client expects before approving an operation.",
    )


class RecommendationOperationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, help_text="Unique identifier for the recommendation operation.")
    sequence = serializers.IntegerField(read_only=True, help_text="1-based sequence of the operation within the recommendation.")
    operation_type = serializers.CharField(read_only=True, help_text="Operation type such as replace_exercise or update_exercise.")
    status = serializers.CharField(read_only=True, help_text="Current state of the operation.")
    payload = serializers.JSONField(read_only=True, help_text="Operation-specific payload describing the proposed workout change.")
    display_text = serializers.CharField(read_only=True, help_text="Human-readable summary of the operation.")


class RecommendationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, help_text="Unique identifier for the recommendation.")
    user_id = serializers.CharField(read_only=True, help_text="User identifier that owns the recommendation.")
    workout_id = serializers.UUIDField(read_only=True, help_text="Workout identifier the recommendation applies to.")
    snapshot_version = serializers.CharField(read_only=True, help_text="Workout version used when the recommendation was generated.")
    status = serializers.CharField(read_only=True, help_text="Rollup status for the recommendation and its operations.")
    summary = serializers.CharField(read_only=True, help_text="Short summary of the recommendation.")
    reason = serializers.CharField(read_only=True, allow_blank=True, help_text="Longer reason explaining why the recommendation was generated.")
    operations = RecommendationOperationSerializer(many=True, read_only=True, help_text="Ordered list of recommendation operations.")
    created_at = serializers.DateTimeField(read_only=True, help_text="Timestamp when the recommendation was created.")
    updated_at = serializers.DateTimeField(read_only=True, help_text="Timestamp when the recommendation was last updated.")
