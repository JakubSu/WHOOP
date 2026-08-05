from rest_framework import serializers


class CoachActivitySerializer(serializers.Serializer):
    """Serializes a sanitized assistant tool activity."""

    id = serializers.UUIDField(read_only=True)
    kind = serializers.ChoiceField(
        choices=[
            "recovery_data",
            "training_data",
            "workout_data",
            "recommendation",
            "other",
        ],
        read_only=True,
    )
    label = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(
        choices=["running", "completed", "failed"], read_only=True
    )


class CoachOperationSerializer(serializers.Serializer):
    """Serializes a recommendation operation proposed by the assistant."""

    id = serializers.UUIDField(read_only=True)
    recommendation_id = serializers.UUIDField(read_only=True)
    type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class CoachMessageSerializer(serializers.Serializer):
    """Serializes a visible chat message."""

    id = serializers.UUIDField(read_only=True)
    role = serializers.ChoiceField(choices=["user", "assistant"], read_only=True)
    content = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    activities = CoachActivitySerializer(many=True, read_only=True)
    operations = CoachOperationSerializer(many=True, read_only=True)


class MessagePageSerializer(serializers.Serializer):
    """Serializes one backward-paginated message page."""

    next = serializers.CharField(read_only=True, allow_null=True)
    results = CoachMessageSerializer(many=True, read_only=True)


class MessageCreateSerializer(serializers.Serializer):
    """Validates the new user message sent to the coach."""

    content = serializers.CharField(allow_blank=False, trim_whitespace=True)
