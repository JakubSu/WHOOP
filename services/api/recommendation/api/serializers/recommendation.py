from typing import Any, cast

from rest_framework import serializers

from recommendation.models import Recommendation, RecommendationOperation
from training.models import Workout, WorkoutExercise


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
        if (
            operation.operation_type
            in {
                RecommendationOperation.OperationType.ADD_EXERCISE,
                RecommendationOperation.OperationType.UPDATE_EXERCISE,
            }
            and payload.get("position") is not None
        ):
            payload["position"] += 1
        return payload


class CoachRecommendationCardSerializer(serializers.Serializer):
    """Serializes the compact recommendation reference embedded in coach messages."""

    id = serializers.UUIDField(read_only=True)
    status = serializers.ChoiceField(
        choices=Recommendation.Status.choices, read_only=True
    )
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
    """Serializes recommendation metadata; workouts remain owned by Training."""

    id = serializers.UUIDField(
        read_only=True, help_text="Unique identifier for the recommendation."
    )
    status = serializers.ChoiceField(
        choices=Recommendation.Status.choices, read_only=True
    )
    summary = serializers.CharField(
        read_only=True, help_text="Short summary of the recommendation."
    )
    groups = serializers.SerializerMethodField()
    operations = serializers.SerializerMethodField()

    def get_groups(self, recommendation: Recommendation) -> list[dict[str, Any]]:
        """Maps operations to Workout API targets or an unpersisted workout draft."""

        operations = list(recommendation.operations.order_by("created_at"))
        exercise_workouts = {
            str(exercise.id): str(exercise.workout_id)
            for exercise in WorkoutExercise.objects.filter(
                pk__in=[
                    operation.payload["workout_exercise_id"]
                    for operation in operations
                    if operation.payload.get("workout_exercise_id")
                ]
            )
        }
        workout_ids = {
            workout_id
            for operation in operations
            if (workout_id := _operation_workout_id(operation)) is not None
        } | set(exercise_workouts.values())
        workout_names = {
            str(workout.id): workout.name
            for workout in Workout.objects.filter(pk__in=workout_ids)
        }
        groups: dict[str, dict[str, Any]] = {}
        for operation in operations:
            payload = operation.payload
            temporary_id = _new_workout_reference_from_operation(operation)
            if operation.operation_type == RecommendationOperation.OperationType.ADD_WORKOUT:
                temporary_id = str(payload["temporary_id"])
            workout_id = _operation_workout_id(operation)
            source_workout_id = exercise_workouts.get(
                str(payload.get("workout_exercise_id"))
            )
            if workout_id is None:
                workout_id = source_workout_id
            group_workout_ids = (
                [temporary_id]
                if temporary_id
                else list(dict.fromkeys(filter(None, [source_workout_id, workout_id])))
            )
            if not group_workout_ids:
                continue
            if temporary_id:
                add_workout = next(
                    (
                        item
                        for item in operations
                        if item.operation_type == RecommendationOperation.OperationType.ADD_WORKOUT
                        and str(item.payload["temporary_id"]) == temporary_id
                    ),
                    None,
                )
                if add_workout is None:
                    continue
                created_workout_id = add_workout.payload.get("created_workout_id")
                target: dict[str, Any] = (
                    {"kind": "existing", "workout_id": str(created_workout_id)}
                    if created_workout_id
                    else {
                        "kind": "new",
                        "temporary_id": temporary_id,
                        "draft": {
                            "name": add_workout.payload["name"],
                            "date": str(add_workout.payload["date"]),
                            "expected_time": add_workout.payload.get("expected_time", 0),
                        },
                    }
                )
                title = add_workout.payload["name"]
                group = groups.setdefault(
                    temporary_id,
                    {
                        "id": temporary_id,
                        "title": title,
                        "target": target,
                        "operation_ids": [],
                    },
                )
                group["operation_ids"].append(str(operation.id))
                continue
            for group_workout_id in group_workout_ids:
                target = {"kind": "existing", "workout_id": str(group_workout_id)}
                title = workout_names.get(str(group_workout_id), "Workout")
                group = groups.setdefault(
                    str(group_workout_id),
                    {
                        "id": str(group_workout_id),
                        "title": title,
                        "target": target,
                        "operation_ids": [],
                    },
                )
                group["operation_ids"].append(str(operation.id))
        return list(groups.values())

    def get_operations(self, recommendation: Recommendation) -> list[dict[str, Any]]:
        """Returns the ledger so the client can hide resolved overlays."""

        operations = list(recommendation.operations.order_by("created_at"))
        serialized_operations = cast(
            list[dict[str, Any]],
            RecommendationOperationSerializer(operations, many=True).data,
        )
        return serialized_operations


def _operation_workout_id(operation: RecommendationOperation) -> str | None:
    payload = operation.payload
    if payload.get("workout_id"):
        return str(payload["workout_id"])
    if payload.get("target_workout_id"):
        return str(payload["target_workout_id"])
    workout = payload.get("workout")
    if workout and workout["kind"] == "existing":
        return str(workout["workout_id"])
    return None


def _new_workout_reference_from_operation(
    operation: RecommendationOperation,
) -> str | None:
    if operation.operation_type != RecommendationOperation.OperationType.ADD_EXERCISE:
        return None
    workout = operation.payload.get("workout")
    if workout and workout["kind"] == "new":
        return workout["temporary_id"]
    return None
