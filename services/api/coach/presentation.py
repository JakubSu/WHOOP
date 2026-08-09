from typing import Any, Final

from ai.runner import ActivityKind

TOOL_PRESENTATIONS: Final[dict[ActivityKind, str]] = {
    "recovery_data": "Fetching your recovery data…",
    "training_data": "Reviewing your recent training…",
    "workout_data": "Reviewing your workout…",
    "recommendation": "Creating recommendations…",
    "other": "Working on your request…",
}


def safe_activity_presentation(kind: str) -> tuple[ActivityKind, str]:
    safe_kind: ActivityKind = kind if kind in TOOL_PRESENTATIONS else "other"  # type: ignore[assignment]
    return safe_kind, TOOL_PRESENTATIONS[safe_kind]


def recommendation_transitions_for_message(message: Any) -> list[dict[str, Any]]:
    """Builds the stream updates for cards superseded by this message's recommendation."""

    from recommendation.models import Recommendation

    attached = getattr(message, "coach_card_recommendations", None)
    if attached is None:
        attached = list(message.recommendations.all())
    if not attached:
        return []
    return [
        {
            "recommendation_id": str(item.id),
            "status": item.status,
            "actionable": False,
            "replaced_by_recommendation_id": str(attached[0].id),
        }
        for item in Recommendation.objects.filter(replaced_by=attached[0])
    ]
