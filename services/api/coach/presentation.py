from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Final

from ai.runner import ActivityKind


@dataclass(frozen=True)
class ToolPresentation:
    """The safe, user-facing presentation for one Coach tool."""

    kind: ActivityKind
    label: str


TOOL_PRESENTATIONS: Final[dict[str, ToolPresentation]] = {
    "search_workouts": ToolPresentation("workout_data", "Searching your workouts…"),
    "get_workout": ToolPresentation("workout_data", "Loading workout details…"),
    "get_whoop_summary": ToolPresentation(
        "recovery_data", "Fetching your recovery data…"
    ),
    "search_exercises": ToolPresentation(
        "training_data", "Searching your exercise library…"
    ),
    "get_exercise": ToolPresentation(
        "training_data", "Checking the selected exercise…"
    ),
    "get_active_recommendation": ToolPresentation(
        "recommendation", "Checking your active recommendation…"
    ),
    "create_recommendation": ToolPresentation(
        "recommendation", "Preparing your recommendation…"
    ),
    "request_ui_action": ToolPresentation(
        "training_data", "Asking you to choose an exercise…"
    ),
}

_FALLBACK_PRESENTATIONS: Final[dict[ActivityKind, str]] = {
    "recovery_data": "Fetching your recovery data…",
    "training_data": "Reviewing your recent training…",
    "workout_data": "Reviewing your workout…",
    "recommendation": "Creating recommendations…",
    "other": "Working on your request…",
}


def safe_activity_presentation(
    kind: str, tool_name: str | None = None
) -> tuple[ActivityKind, str]:
    """Return an allowlisted activity presentation without trusting runner text."""

    if tool_name is not None and (presentation := TOOL_PRESENTATIONS.get(tool_name)):
        return presentation.kind, presentation.label
    safe_kind: ActivityKind = kind if kind in _FALLBACK_PRESENTATIONS else "other"  # type: ignore[assignment]
    return safe_kind, _FALLBACK_PRESENTATIONS[safe_kind]


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


def updated_messages_for_message(
    message: Any, *, additional_message_ids: Iterable[Any] = ()
) -> list[Any]:
    """Returns prior chat messages changed by this turn or its trusted input."""

    from coach.models import CoachMessage
    from recommendation.models import Recommendation

    attached = getattr(message, "coach_card_recommendations", None)
    if attached is None:
        attached = list(message.recommendations.all())
    changed_message_ids = (
        {
            item.coach_message_id
            for item in Recommendation.objects.select_related("coach_message").filter(
                replaced_by=attached[0], coach_message__isnull=False
            )
        }
        if attached
        else set()
    )
    changed_message_ids.update(additional_message_ids)
    if not changed_message_ids:
        return []
    return list(
        CoachMessage.objects.filter(pk__in=changed_message_ids)
        .prefetch_related("ui_actions")
        .order_by("created_at", "id")
    )
