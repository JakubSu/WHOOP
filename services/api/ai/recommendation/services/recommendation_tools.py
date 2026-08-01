from __future__ import annotations

from typing import Any, Protocol

from django.db import transaction
from django.db.models import Q
from recommendation import services as recommendation_services
from recommendation.models import Recommendation
from training.models import Exercise, Workout
from whoop.exceptions import WhoopConnectionNotFound, WhoopError
from whoop.workflows.summary import disconnected_summary

from ai.recommendation.schemas import WorkoutPatchDraft
from ai.recommendation.services.workout_patch_generator import WorkoutPatchGenerator


class WorkoutPatchDraftGenerator(Protocol):
    def generate(self, context: dict[str, Any]) -> WorkoutPatchDraft: ...


def build_workout_recommendation_context(
    user_id: str, workout_id: str
) -> dict[str, Any]:
    try:
        workout = Workout.objects.prefetch_related("workout_exercises__exercise").get(
            pk=workout_id, user_id=user_id
        )
    except Workout.DoesNotExist as exc:
        raise recommendation_services.RecommendationNotFound(
            "Workout was not found."
        ) from exc

    return {
        "current_workout": {
            "id": str(workout.id),
            "version": workout.updated_at.isoformat(),
            "plan": str(workout.plan_id) if workout.plan_id else None,
            "name": workout.name,
            "date": workout.date.isoformat() if workout.date else None,
            "expected_time": workout.expected_time,
            "exercises": [
                {
                    "workout_exercise_id": str(workout_exercise.id),
                    "exercise_id": str(workout_exercise.exercise_id),
                    "name": workout_exercise.exercise.name,
                    "muscle_group": workout_exercise.exercise.muscle_group,
                    "default_sets": workout_exercise.exercise.default_sets,
                    "default_reps": workout_exercise.exercise.default_reps,
                    "default_time": workout_exercise.exercise.default_time,
                    "prescription_type": workout_exercise.exercise.prescription_type,
                    "exercise_notes": workout_exercise.exercise.notes,
                    "sets": workout_exercise.sets,
                    "reps": workout_exercise.reps,
                    "time": workout_exercise.time,
                    "weight": float(workout_exercise.weight)
                    if workout_exercise.weight is not None
                    else None,
                    "weight_unit": workout_exercise.weight_unit,
                    "note": workout_exercise.note,
                }
                for workout_exercise in workout.workout_exercises.all().order_by(
                    "sort_order", "created_at", "exercise__name"
                )
            ],
        },
        "available_exercises": [
            _exercise_catalog_item(exercise)
            for exercise in Exercise.objects.filter(
                Q(user_id=user_id) | Q(user_id="")
            ).order_by("name")
        ],
        "whoop_summary": build_whoop_summary(user_id),
        "allowed_operations": [
            "add_exercise",
            "remove_exercise",
            "replace_exercise",
            "update_exercise",
            "move_exercise",
            "add_workout",
            "remove_workout",
            "update_workout",
            "revise_workout",
        ],
    }


def build_whoop_summary(user_id: str) -> dict[str, Any]:
    from whoop import services as whoop_services

    try:
        return whoop_services.create_summary_service().execute(user_id)
    except WhoopConnectionNotFound:
        return disconnected_summary()
    except WhoopError as exc:
        return {
            "connected": False,
            "detail": f"WHOOP summary unavailable: {exc}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "connected": False,
            "detail": f"WHOOP summary unavailable: {exc}",
        }


@transaction.atomic
def generate_recommendation_for_workout(
    user_id: str,
    workout_id: str,
    *,
    generator: WorkoutPatchDraftGenerator | None = None,
) -> Recommendation:
    context = build_workout_recommendation_context(user_id, workout_id)
    draft = (generator or WorkoutPatchGenerator()).generate(context)
    return propose_workout_changes(
        user_id=user_id,
        workout_id=workout_id,
        draft=draft,
        snapshot_version=str(context["current_workout"]["version"]),
    )


def propose_workout_changes(
    *,
    user_id: str,
    workout_id: str,
    draft: WorkoutPatchDraft | dict[str, Any],
    snapshot_version: str | None = None,
    source: str = Recommendation.Source.DAILY_RECOMMENDATION,
    coach_conversation_id: str | None = None,
    coach_message_id: str | None = None,
) -> Recommendation:
    if not isinstance(draft, WorkoutPatchDraft):
        draft = WorkoutPatchDraft.model_validate(draft)
    return recommendation_services.create_recommendation_from_workout_patch(
        user_id=user_id,
        workout_id=workout_id,
        draft=draft,
        snapshot_version=snapshot_version,
        source=source,
        coach_conversation_id=coach_conversation_id,
        coach_message_id=coach_message_id,
    )


def _exercise_catalog_item(exercise: Exercise) -> dict[str, Any]:
    return {
        "id": str(exercise.id),
        "name": exercise.name,
        "prescription_type": exercise.prescription_type,
        "default_sets": exercise.default_sets,
        "default_reps": exercise.default_reps,
        "muscle_group": exercise.muscle_group,
        "default_time": exercise.default_time,
        "notes": exercise.notes,
    }
