from typing import Any, cast

from rest_framework import serializers

from coach.models import CoachMessage
from recommendation.models import Recommendation


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


class CoachMessageSerializer(serializers.Serializer):
    """Serializes a visible chat message."""

    id = serializers.UUIDField(read_only=True)
    role = serializers.ChoiceField(choices=["user", "assistant"], read_only=True)
    content = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    activities = serializers.SerializerMethodField()
    recommendation = serializers.SerializerMethodField()

    def get_activities(self, message: CoachMessage) -> list[dict[str, Any]]:
        """Exposes activity logs only for assistant messages."""

        activity_log = (
            message.activity_log if message.role == CoachMessage.Role.ASSISTANT else []
        )
        return cast(
            list[dict[str, Any]], CoachActivitySerializer(activity_log, many=True).data
        )

    def get_recommendation(self, message: CoachMessage) -> dict[str, Any] | None:
        """Serializes the single recommendation card attached to an assistant message."""

        if message.role != CoachMessage.Role.ASSISTANT:
            return None
        from recommendation.api.serializers import CoachRecommendationCardSerializer

        attached = cast(
            list[Recommendation] | None,
            getattr(message, "coach_card_recommendations", None),
        )
        if attached is None:
            attached = list(message.recommendations.all())
        return (
            cast(dict[str, Any], CoachRecommendationCardSerializer(attached[0]).data)
            if attached
            else None
        )


class MessagePageSerializer(serializers.Serializer):
    """Serializes one backward-paginated message page."""

    next = serializers.CharField(read_only=True, allow_null=True)
    results = CoachMessageSerializer(many=True, read_only=True)


class MessageCreateSerializer(serializers.Serializer):
    """Validates the new user message sent to the coach."""

    content = serializers.CharField(allow_blank=False, trim_whitespace=True)
