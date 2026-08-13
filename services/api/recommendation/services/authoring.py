from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction

from recommendation.contracts import (
    ActiveRecommendation,
    AddExerciseOperation,
    AddWorkoutOperation,
    RecommendationDraft,
    RemoveExerciseOperation,
    RemoveWorkoutOperation,
    UpdateExerciseOperation,
    UpdateWorkoutOperation,
)
from recommendation.models import Recommendation, RecommendationOperation
from recommendation.services.errors import (
    RecommendationConflict,
    RecommendationValidationError,
)
from recommendation.services.presentation import refresh_coach_card_snapshot
from training.models import Exercise, Workout, WorkoutExercise


@transaction.atomic
def create_recommendation(
    *,
    user: Any,
    conversation: Any,
    draft: RecommendationDraft | dict[str, Any],
    coach_message: Any = None,
    source: str = Recommendation.Source.COACH_CHAT,
    # Omit both only for non-AI creation flows; AI tool calls must provide both
    # IDs so retries are idempotent and failed runs can be expired.
    run_id: UUID | None = None,
    tool_call_id: str | None = None,
    replaces_recommendation_id: str | UUID | None = None,
) -> Recommendation:
    """Creates a complete next proposal and atomically supersedes the active one."""

    draft = RecommendationDraft.model_validate(draft)
    _validate_conversation(user=user, conversation=conversation)
    if not draft.operations:
        raise RecommendationValidationError(
            "A recommendation must include at least one operation."
        )
    if (run_id is None) != (tool_call_id is None):
        raise RecommendationValidationError(
            "A recommendation tool call requires both run and tool call IDs."
        )

    if run_id is not None and tool_call_id is not None:
        existing = (
            Recommendation.objects.select_for_update()
            .filter(run_id=run_id, tool_call_id=tool_call_id)
            .first()
        )
        if existing is not None:
            if (
                existing.user_id != user.id
                or existing.conversation_id != conversation.id
            ):
                raise RecommendationValidationError(
                    "Recommendation tool call is outside the active conversation."
                )
            return existing
    _validate_draft_targets(user=user, draft=draft)
    active = (
        Recommendation.objects.select_for_update()
        .filter(
            user=user,
            status=Recommendation.Status.ACTIVE,
        )
        .first()
    )
    if replaces_recommendation_id is not None:
        if active is None or str(active.id) != str(replaces_recommendation_id):
            raise RecommendationConflict(
                "The active recommendation changed. Load it again before replacing it."
            )
    elif active is not None:
        raise RecommendationConflict(
            "Load the active recommendation before replacing it."
        )
    if active is not None:
        from django.utils import timezone

        superseded_at = timezone.now()
        active.status = Recommendation.Status.SUPERSEDED
        active.superseded_at = superseded_at
        active.save(update_fields=["status", "superseded_at", "updated_at"])
        RecommendationOperation.objects.filter(
            recommendation=active,
            status=RecommendationOperation.Status.PENDING,
        ).update(
            status=RecommendationOperation.Status.STALE,
            resolved_at=superseded_at,
            updated_at=superseded_at,
        )
        refresh_coach_card_snapshot(active)
    try:
        with transaction.atomic():
            recommendation = Recommendation.objects.create(
                user=user,
                conversation=conversation,
                coach_message=coach_message,
                summary=draft.summary,
                source=source,
                run_id=run_id,
                tool_call_id=tool_call_id,
            )
    except IntegrityError as exc:
        if run_id is None or tool_call_id is None:
            raise
        recommendation = Recommendation.objects.get(
            run_id=run_id, tool_call_id=tool_call_id
        )
        if (
            recommendation.user_id != user.id
            or recommendation.conversation_id != conversation.id
        ):
            raise RecommendationValidationError(
                "Recommendation tool call is outside the active conversation."
            ) from exc
        return recommendation
    for item in draft.operations:
        RecommendationOperation.objects.create(
            recommendation=recommendation,
            operation_type=item.operation_type,
            reason=item.reason,
            payload=item.payload.model_dump(mode="json"),
        )
    refresh_coach_card_snapshot(recommendation)
    if active is not None:
        active.replaced_by = recommendation
        active.save(update_fields=["replaced_by", "updated_at"])
    return recommendation


@transaction.atomic
def attach_recommendation_to_coach_message(
    *, user: Any, conversation: Any, coach_message: Any, recommendation_id: str | UUID
) -> Recommendation:
    """Links an active tool-created recommendation to its completed coach response."""

    try:
        recommendation = Recommendation.objects.get(
            pk=recommendation_id,
            user=user,
            conversation=conversation,
            coach_message__isnull=True,
            status=Recommendation.Status.ACTIVE,
        )
    except Recommendation.DoesNotExist as exc:
        raise RecommendationValidationError(
            "Recommendation was not created for this coach conversation."
        ) from exc
    recommendation.coach_message = coach_message
    recommendation.save(update_fields=["coach_message", "updated_at"])
    return recommendation


def get_active_recommendation(
    *, user: Any, conversation: Any
) -> ActiveRecommendation | None:
    """Returns the user's copyable pending proposal for the coach tool."""

    _validate_conversation(user=user, conversation=conversation)
    recommendation = (
        Recommendation.objects.filter(
            user=user,
            status=Recommendation.Status.ACTIVE,
        )
        .prefetch_related("operations")
        .first()
    )
    if recommendation is None:
        return None
    pending = recommendation.operations.filter(
        status=RecommendationOperation.Status.PENDING
    ).order_by("created_at")
    if not pending.exists():
        return None
    return ActiveRecommendation(
        recommendation_id=recommendation.id,
        draft=RecommendationDraft.model_validate(
            {
                "summary": recommendation.summary,
                "operations": [
                    {
                        "operation_type": operation.operation_type,
                        "reason": operation.reason,
                        "payload": operation.payload,
                    }
                    for operation in pending
                ],
            }
        ),
    )


def _validate_conversation(*, user: Any, conversation: Any) -> None:
    if conversation is None or conversation.user_id != user.id:
        raise RecommendationValidationError("Coach conversation was not found.")


def _validate_draft_targets(*, user: Any, draft: RecommendationDraft) -> None:
    # Resolve temporary workout references before validating dependent operations;
    # the AI is not required to return operations in dependency order.
    temporary_workouts = {
        str(item.payload.temporary_id)
        for item in draft.operations
        if isinstance(item, AddWorkoutOperation)
    }
    for item in draft.operations:
        if isinstance(item, AddWorkoutOperation):
            continue
        if isinstance(item, UpdateWorkoutOperation | RemoveWorkoutOperation):
            _require_user_workout(user=user, workout_id=item.payload.workout_id)
        elif isinstance(item, AddExerciseOperation):
            if item.payload.workout.kind == "existing":
                _require_user_workout(
                    user=user, workout_id=item.payload.workout.workout_id
                )
            elif item.payload.workout.temporary_id not in temporary_workouts:
                raise RecommendationValidationError(
                    "Temporary workout was not created in this recommendation."
                )
            if not Exercise.objects.filter(
                pk=item.payload.exercise_id, user_id__in=[str(user.id), ""]
            ).exists():
                raise RecommendationValidationError("Exercise was not found.")
        elif isinstance(item, UpdateExerciseOperation):
            _require_user_workout_exercise(
                user=user, workout_exercise_id=item.payload.workout_exercise_id
            )
            if item.payload.target_workout_id is not None:
                _require_user_workout(
                    user=user, workout_id=item.payload.target_workout_id
                )
        elif isinstance(item, RemoveExerciseOperation):
            _require_user_workout_exercise(
                user=user, workout_exercise_id=item.payload.workout_exercise_id
            )


def _require_user_workout(*, user: Any, workout_id: UUID) -> None:
    if not Workout.objects.filter(pk=workout_id, user_id=str(user.id)).exists():
        raise RecommendationValidationError("Workout was not found.")


def _require_user_workout_exercise(*, user: Any, workout_exercise_id: UUID) -> None:
    if not WorkoutExercise.objects.filter(
        pk=workout_exercise_id, workout__user_id=str(user.id)
    ).exists():
        raise RecommendationValidationError("Workout exercise was not found.")
