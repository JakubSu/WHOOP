from rest_framework import serializers


class AcceptRecommendationSerializer(serializers.Serializer):
    expected_workout_version = serializers.CharField(
        required=False,
        allow_blank=False,
        help_text="Optional workout version the client expects before accepting the recommendation.",
    )


class RecommendationErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class RecommendationUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["pending", "applied", "rejected", "stale", "failed"],
        required=False,
        help_text="Recommendation status.",
    )


class RecommendationSerializer(serializers.Serializer):
    id = serializers.UUIDField(
        read_only=True, help_text="Unique identifier for the recommendation."
    )
    user_id = serializers.CharField(
        read_only=True, help_text="User identifier that owns the recommendation."
    )
    workout_id = serializers.UUIDField(
        read_only=True, help_text="Workout identifier the recommendation applies to."
    )
    snapshot_version = serializers.CharField(
        read_only=True,
        help_text="Workout version used when the recommendation was generated.",
    )
    status = serializers.CharField(read_only=True, help_text="Recommendation status.")
    summary = serializers.CharField(
        read_only=True, help_text="Short summary of the recommendation."
    )
    reason = serializers.CharField(
        read_only=True,
        allow_blank=True,
        help_text="Longer reason explaining why the recommendation was generated.",
    )
    source = serializers.CharField(
        read_only=True,
        help_text="Recommendation source such as daily_recommendation or coach_chat.",
    )
    coach_conversation_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
        help_text="Coach conversation that created this recommendation, when applicable.",
    )
    coach_message_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
        help_text="Coach assistant message that created this recommendation, when applicable.",
    )
    operation_type = serializers.CharField(
        read_only=True, help_text="Domain operation type."
    )
    payload = serializers.JSONField(
        read_only=True,
        help_text="Operation-specific payload describing the proposed workout change.",
    )
    display_text = serializers.CharField(
        read_only=True, help_text="Human-readable summary of the operation."
    )
    created_at = serializers.DateTimeField(
        read_only=True, help_text="Timestamp when the recommendation was created."
    )
    updated_at = serializers.DateTimeField(
        read_only=True, help_text="Timestamp when the recommendation was last updated."
    )
