from typing import Any, cast

from rest_framework import serializers

from recommendation.models import Recommendation, RecommendationOperation


class RecommendationOperationSerializer(serializers.Serializer):
    """Serializes one recommendation operation for the actionable detail view."""

    id = serializers.UUIDField(read_only=True)
    status = serializers.ChoiceField(
        choices=RecommendationOperation.Status.choices, read_only=True
    )
    operation_type = serializers.ChoiceField(
        choices=RecommendationOperation.OperationType.choices, read_only=True
    )
    display_text = serializers.CharField(read_only=True)
    reason = serializers.CharField(read_only=True)
    payload = serializers.SerializerMethodField()

    def get_payload(self, operation: RecommendationOperation) -> dict[str, Any]:
        """Converts stored zero-based exercise positions for the public response."""

        payload = dict(operation.payload)
        if operation.operation_type in {
            RecommendationOperation.OperationType.ADD_EXERCISE,
            RecommendationOperation.OperationType.UPDATE_EXERCISE,
        } and payload.get("position") is not None:
            payload["position"] += 1
        return payload


class CoachRecommendationCardSerializer(serializers.Serializer):
    """Serializes the compact recommendation reference embedded in coach messages."""

    id = serializers.UUIDField(read_only=True)
    status = serializers.ChoiceField(choices=Recommendation.Status.choices, read_only=True)
    actionable = serializers.SerializerMethodField()
    coach_card_snapshot = serializers.JSONField(read_only=True)

    def get_actionable(self, recommendation: Recommendation) -> bool:
        """Uses the message-list annotation when present, otherwise derives it."""

        has_pending_operations = getattr(recommendation, "has_pending_operations", None)
        if has_pending_operations is None:
            has_pending_operations = recommendation.operations.filter(
                status=RecommendationOperation.Status.PENDING
            ).exists()
        return recommendation.status == Recommendation.Status.ACTIVE and bool(
            has_pending_operations
        )


class RecommendationSerializer(serializers.Serializer):
    """Serializes the full actionable recommendation response."""

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
    operations = serializers.SerializerMethodField()

    def get_operations(self, recommendation: Recommendation) -> list[dict[str, Any]]:
        """Omits stale rows and nests new-workout exercise additions under their parent."""

        operations = list(
            recommendation.operations.exclude(
                status=RecommendationOperation.Status.STALE
            ).order_by("created_at")
        )
        serialized_operations = cast(
            list[dict[str, Any]],
            RecommendationOperationSerializer(operations, many=True).data,
        )
        children_by_temp: dict[str, list[dict[str, Any]]] = {}
        result: list[dict[str, Any]] = []
        for operation in serialized_operations:
            temporary_workout_id = (
                operation["payload"].get("temporary_workout_id")
                if operation["operation_type"]
                == RecommendationOperation.OperationType.ADD_EXERCISE
                else None
            )
            if temporary_workout_id:
                children_by_temp.setdefault(str(temporary_workout_id), []).append(operation)
            else:
                result.append(operation)
        for operation in result:
            if operation["operation_type"] == RecommendationOperation.OperationType.ADD_WORKOUT:
                operation["exercise_operations"] = children_by_temp.pop(
                    str(operation["payload"]["temporary_id"]), []
                )
        return result
