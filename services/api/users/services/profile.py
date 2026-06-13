from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model


class GetProfileService:
    def execute(self, *, user_id: str) -> Any:
        return _get_user(user_id)


class UpdateProfileService:
    def execute(self, *, user_id: str, display_name: str | None = None) -> Any:
        user = _get_user(user_id)
        if display_name is not None:
            user.display_name = display_name
        user.save(update_fields=["display_name", "updated_at"])
        return user


class SetWhoopUserIdService:
    def execute(self, *, user_id: str, whoop_user_id: str | int) -> Any:
        user = _get_user(user_id)
        user.whoop_user_id = str(whoop_user_id)
        user.save(update_fields=["whoop_user_id", "updated_at"])
        return user


class ClearWhoopUserIdService:
    def execute(self, *, user_id: str) -> Any:
        user = _get_user(user_id)
        user.whoop_user_id = ""
        user.save(update_fields=["whoop_user_id", "updated_at"])
        return user


def _get_user(user_id: str) -> Any:
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise ValueError("User was not found.") from exc
