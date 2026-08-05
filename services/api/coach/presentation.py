from typing import Final

from coach.runner import ActivityKind

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
