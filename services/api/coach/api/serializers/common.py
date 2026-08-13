from rest_framework import serializers


class CursorQuerySerializer(serializers.Serializer):
    """Validates an optional opaque pagination cursor."""

    cursor = serializers.CharField(required=False, allow_blank=False)
