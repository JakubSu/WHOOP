from rest_framework import serializers


class ConversationSerializer(serializers.Serializer):
    """Serializes a single coach conversation."""

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ConversationSummarySerializer(serializers.Serializer):
    """Serializes a conversation for the history list."""

    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    last_message_preview = serializers.CharField(read_only=True, allow_null=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ConversationPageSerializer(serializers.Serializer):
    """Serializes one page of conversation summaries."""

    next = serializers.CharField(read_only=True, allow_null=True)
    results = ConversationSummarySerializer(many=True, read_only=True)


class ConversationPatchSerializer(serializers.Serializer):
    """Validates supported updates to a coach conversation."""

    title = serializers.CharField(max_length=200, allow_blank=False, trim_whitespace=True)
