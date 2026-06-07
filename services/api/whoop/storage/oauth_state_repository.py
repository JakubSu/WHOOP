from __future__ import annotations

from datetime import timedelta
from secrets import token_urlsafe

from django.utils import timezone

from whoop.models import WhoopOAuthState


class WhoopOAuthStateRepository:
    def create(self, *, user_id: str, ttl_seconds: int) -> WhoopOAuthState:
        now = timezone.now()
        return WhoopOAuthState.objects.create(
            state=token_urlsafe(32),
            user_id=user_id,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

    def consume(self, *, state: str) -> WhoopOAuthState | None:
        now = timezone.now()
        mapping = (
            WhoopOAuthState.objects.select_for_update()
            .filter(
                state=state,
                consumed_at__isnull=True,
                expires_at__gt=now,
            )
            .first()
        )
        if mapping is None:
            return None

        mapping.consumed_at = now
        mapping.save(update_fields=["consumed_at"])
        return mapping
