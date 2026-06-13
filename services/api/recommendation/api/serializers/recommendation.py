from rest_framework import serializers


class ApproveRecommendationSerializer(serializers.Serializer):
    expected_workout_version = serializers.CharField(required=False, allow_blank=False)

