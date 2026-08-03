from rest_framework import serializers


class RecommendationSerializer(serializers.Serializer):
    id = serializers.UUIDField(
        read_only=True, help_text="Unique identifier for the recommendation."
    )
    summary = serializers.CharField(
        read_only=True, help_text="Short summary of the recommendation."
    )
    reason = serializers.CharField(
        read_only=True,
        allow_blank=True,
        help_text="Longer reason explaining why the recommendation was generated.",
    )
    operations = serializers.ListField(read_only=True)
