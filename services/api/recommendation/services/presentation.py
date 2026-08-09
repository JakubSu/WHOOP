from typing import Any

from recommendation.models import Recommendation, RecommendationOperation
from training.models import Workout, WorkoutExercise


def serialize_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    """Projects a recommendation into the public REST response shape."""

    operations = list(
        recommendation.operations.exclude(
            status=RecommendationOperation.Status.STALE
        ).order_by("created_at")
    )
    children_by_temp: dict[str, list[dict[str, Any]]] = {}
    result: list[dict[str, Any]] = []
    for operation in operations:
        data = _serialize_operation(operation)
        temp_workout_id = (
            data["payload"].get("temporary_workout_id")
            if operation.operation_type == "add_exercise"
            else None
        )
        if temp_workout_id:
            children_by_temp.setdefault(str(temp_workout_id), []).append(data)
        else:
            result.append(data)
    for operation in result:
        if operation["operation_type"] == "add_workout":
            operation["exercise_operations"] = children_by_temp.pop(
                str(operation["payload"]["temporary_id"]), []
            )
    return {
        "id": str(recommendation.id),
        "summary": recommendation.summary,
        "reason": recommendation.reason,
        "operations": result,
    }


def serialize_coach_recommendation(recommendation: Recommendation) -> dict[str, Any]:
    """Builds a message-owned recommendation card grouped by affected workout."""

    operations = list(recommendation.operations.order_by("created_at"))
    workout_exercise_ids = [
        operation.payload.get("workout_exercise_id")
        for operation in operations
        if operation.payload.get("workout_exercise_id")
    ]
    workout_by_exercise_id = {
        str(exercise.id): exercise.workout
        for exercise in WorkoutExercise.objects.select_related("workout").filter(
            pk__in=workout_exercise_ids
        )
    }
    workout_ids = [
        operation.payload.get("workout_id")
        for operation in operations
        if operation.payload.get("workout_id")
    ]
    workout_by_id = {
        str(workout.id): workout
        for workout in Workout.objects.filter(pk__in=workout_ids)
    }
    groups: dict[str, dict[str, Any]] = {}
    for operation in operations:
        payload = operation.payload
        temporary_id = payload.get("temporary_workout_id") or (
            payload.get("temporary_id")
            if operation.operation_type == RecommendationOperation.OperationType.ADD_WORKOUT
            else None
        )
        workout_id = payload.get("workout_id")
        if workout_id is None and payload.get("workout_exercise_id"):
            workout = workout_by_exercise_id.get(str(payload["workout_exercise_id"]))
            workout_id = str(workout.id) if workout else None
        workout = workout_by_id.get(str(workout_id)) if workout_id else None
        key = str(workout_id or temporary_id or "training")
        title = (
            workout.name
            if workout is not None
            else payload.get("name")
            if operation.operation_type == RecommendationOperation.OperationType.ADD_WORKOUT
            else "Training changes"
        )
        group = groups.setdefault(key, {"id": key, "title": title, "operations": []})
        group["operations"].append(_serialize_operation(operation))
    snapshot_groups = recommendation.presentation_snapshot.get("groups", [])
    if snapshot_groups:
        operations_by_id = {
            operation["id"]: operation
            for group in groups.values()
            for operation in group["operations"]
        }
        groups = {
            group["id"]: {
                "id": group["id"],
                "title": group["title"],
                "operations": [
                    operations_by_id[operation_id]
                    for operation_id in group.get("operation_ids", [])
                    if operation_id in operations_by_id
                ],
            }
            for group in snapshot_groups
        }
    return {
        "id": str(recommendation.id),
        "summary": recommendation.summary,
        "reason": recommendation.reason,
        "status": recommendation.status,
        "groups": list(groups.values()),
    }


def build_presentation_snapshot(recommendation: Recommendation) -> dict[str, Any]:
    """Captures stable workout labels and grouping for one chat recommendation card."""

    card = serialize_coach_recommendation(recommendation)
    return {
        "groups": [
            {
                "id": group["id"],
                "title": group["title"],
                "operation_ids": [operation["id"] for operation in group["operations"]],
            }
            for group in card["groups"]
        ]
    }


def _serialize_operation(operation: RecommendationOperation) -> dict[str, Any]:
    """Serializes one ledger row and converts stored zero-based positions for the API."""

    payload = dict(operation.payload)
    if operation.operation_type == "add_exercise" and "position" in payload:
        payload["position"] += 1
    if (
        operation.operation_type == "update_exercise"
        and payload.get("position") is not None
    ):
        payload["position"] += 1
    return {
        "id": str(operation.id),
        "status": operation.status,
        "operation_type": operation.operation_type,
        "display_text": operation.display_text,
        "reason": operation.reason,
        "payload": payload,
    }
