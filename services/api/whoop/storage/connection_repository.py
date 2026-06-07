from __future__ import annotations

from django.utils import timezone

from whoop.models import WhoopConnection
from whoop.storage.token_crypto import TokenCrypto
from whoop.whoop_api.dto import WhoopToken


class WhoopConnectionRepository:
    def __init__(self, token_crypto: TokenCrypto) -> None:
        self.token_crypto = token_crypto

    def get_active_for_user(self, user_id: str) -> WhoopConnection | None:
        try:
            return WhoopConnection.objects.get(user_id=user_id, revoked_at__isnull=True)
        except WhoopConnection.DoesNotExist:
            return None

    def get_tokens(self, connection: WhoopConnection) -> WhoopToken:
        return WhoopToken(
            access_token=self.token_crypto.decrypt(connection.access_token_encrypted),
            refresh_token=self.token_crypto.decrypt(connection.refresh_token_encrypted) or None,
            expires_at=connection.expires_at,
            scope=connection.scopes or None,
        )

    def save_connection(
        self,
        *,
        user_id: str,
        whoop_user_id: str | int,
        token: WhoopToken,
    ) -> WhoopConnection:
        connection, _ = WhoopConnection.objects.update_or_create(
            user_id=user_id,
            defaults={
                "whoop_user_id": str(whoop_user_id),
                "access_token_encrypted": self.token_crypto.encrypt(token.access_token),
                "refresh_token_encrypted": self.token_crypto.encrypt(token.refresh_token),
                "expires_at": token.expires_at,
                "scopes": token.scope or "",
                "revoked_at": None,
            },
        )
        return connection

    def update_tokens(self, connection: WhoopConnection, token: WhoopToken) -> WhoopConnection:
        connection.access_token_encrypted = self.token_crypto.encrypt(token.access_token)
        if token.refresh_token:
            connection.refresh_token_encrypted = self.token_crypto.encrypt(token.refresh_token)
        connection.expires_at = token.expires_at
        if token.scope:
            connection.scopes = token.scope
        connection.save(
            update_fields=[
                "access_token_encrypted",
                "refresh_token_encrypted",
                "expires_at",
                "scopes",
                "updated_at",
            ]
        )
        return connection

    def mark_revoked(self, connection: WhoopConnection) -> WhoopConnection:
        connection.revoked_at = timezone.now()
        connection.save(update_fields=["revoked_at", "updated_at"])
        return connection
