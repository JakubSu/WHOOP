from typing import Any

from recommendation.models import Recommendation, RecommendationOperation
from training.models import Workout, WorkoutExercise


def build_coach_card_snapshot(recommendation: Recommendation) -> dict[str, Any]:
    """Captures the compact, immutable card used in coach chat history."""

    operations = list(recommendation.operations.order_by("created_at"))
    workout_by_exercise_id = {
        str(exercise.id): exercise.workout
        for exercise in WorkoutExercise.objects.select_related("workout").filter(
            pk__in=[
                operation.payload["workout_exercise_id"]
                for operation in operations
                if operation.payload.get("workout_exercise_id")
            ]
        )
    }
    workout_by_id = {
        str(workout.id): workout
        for workout in Workout.objects.filter(
            pk__in=[
                operation.payload["workout_id"]
                for operation in operations
                if operation.payload.get("workout_id")
            ]
        )
    }
    groups: dict[str, dict[str, Any]] = {}
    for operation in operations:
        payload = operation.payload
        workout_id = payload.get("workout_id")
        if workout_id is None and payload.get("workout_exercise_id"):
            workout = workout_by_exercise_id.get(str(payload["workout_exercise_id"]))
            workout_id = str(workout.id) if workout else None
        temporary_id = payload.get("temporary_workout_id") or (
            payload.get("temporary_id")
            if operation.operation_type
            == RecommendationOperation.OperationType.ADD_WORKOUT
            else None
        )
        key = str(workout_id or temporary_id or "training")
        workout = workout_by_id.get(str(workout_id)) if workout_id else None
        group = groups.setdefault(
            key,
            {
                "id": key,
                "title": (
                    workout.name
                    if workout
                    else payload.get("name")
                    if operation.operation_type
                    == RecommendationOperation.OperationType.ADD_WORKOUT
                    else "Training changes"
                ),
                "operation_ids": [],
                "summary": {"total": 0, "added": 0, "updated": 0, "removed": 0},
            },
        )
        group["operation_ids"].append(str(operation.id))
        group["summary"]["total"] += 1
        summary_key = {
            "add": "added",
            "update": "updated",
            "remove": "removed",
        }[operation.operation_type.split("_", maxsplit=1)[0]]
        group["summary"][summary_key] += 1
    return {
        "version": 1,
        "workout_groups": list(groups.values()),
    }
