from rest_framework import serializers


class CoachPageContextSerializer(serializers.Serializer):
    page_type = serializers.CharField()
    context_id = serializers.CharField(required=False, allow_blank=True)


class CoachTurnStreamRequestSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(required=False)
    page_context = CoachPageContextSerializer()
    message = serializers.CharField(allow_blank=False)


class CoachActiveConversationRequestSerializer(serializers.Serializer):
    page_type = serializers.CharField()
    context_id = serializers.CharField(required=False, allow_blank=True)


class CoachMessageSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    role = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    metadata_json = serializers.JSONField(read_only=True)
    recommendation_id = serializers.UUIDField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class CoachConversationMessagesSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField(read_only=True)
    messages = CoachMessageSerializer(many=True, read_only=True)
