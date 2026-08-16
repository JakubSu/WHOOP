"""Serialization for durable, user-facing coach actions."""

from rest_framework import serializers


class UiActionSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    type = serializers.CharField(read_only=True)
    status = serializers.ChoiceField(
        choices=["pending", "resolved", "dismissed"], read_only=True
    )
    payload = serializers.JSONField(read_only=True)
    resolution = serializers.JSONField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    resolved_at = serializers.DateTimeField(read_only=True, allow_null=True)


class UiActionResolveSerializer(serializers.Serializer):
    exercise_id = serializers.UUIDField()
    method = serializers.ChoiceField(
        choices=["created", "selected"], default="selected"
    )
