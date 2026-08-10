"""Invalidate pending proposals when user-owned training data changes."""

from __future__ import annotations

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from recommendation.models import Recommendation, RecommendationOperation
from recommendation.services.presentation import refresh_coach_card_snapshot


def stale_pending_recommendation_operations_for_workout(*, workout_id: str) -> None:
    """Stale pending operations that directly target a changed workout."""

    _invalidate(
        RecommendationOperation.objects.filter(
            status=RecommendationOperation.Status.PENDING,
            payload__workout_id=str(workout_id),
        )
    )


def stale_pending_recommendation_operations_for_workout_exercise(
    *, workout_exercise_id: str
) -> None:
    """Stale pending operations that target a changed workout exercise."""

    _invalidate(
        RecommendationOperation.objects.filter(
            status=RecommendationOperation.Status.PENDING,
            payload__workout_exercise_id=str(workout_exercise_id),
        )
    )


@transaction.atomic
def _invalidate(operations: QuerySet[RecommendationOperation]) -> None:
    rows = list(operations.select_related("recommendation"))
    if not rows:
        return
    now = timezone.now()
    recommendation_ids = {row.recommendation_id for row in rows}
    RecommendationOperation.objects.filter(pk__in=[row.pk for row in rows]).update(
        status=RecommendationOperation.Status.STALE,
        resolved_at=now,
        updated_at=now,
    )
    for recommendation in Recommendation.objects.filter(pk__in=recommendation_ids):
        if not recommendation.operations.filter(
            status=RecommendationOperation.Status.PENDING
        ).exists():
            recommendation.status = Recommendation.Status.COMPLETED
            recommendation.save(update_fields=["status", "updated_at"])
        refresh_coach_card_snapshot(recommendation)
