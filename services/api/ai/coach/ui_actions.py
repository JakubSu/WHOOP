from __future__ import annotations

from typing import Any

from training.models import Workout


class AuthorizeUiActionService:
    def authorize(
        self,
        *,
        user_id: str,
        proposed_actions: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        authorized: list[dict[str, str]] = []
        for action in proposed_actions:
            if action.get("type") != "navigate":
                continue
            if action.get("target") != "workout":
                continue
            workout_id = str(action.get("id") or "")
            if not Workout.objects.filter(pk=workout_id, user_id=user_id).exists():
                continue
            authorized.append(
                {
                    "type": "navigate",
                    "route": f"/workouts/{workout_id}",
                }
            )
        return authorized
