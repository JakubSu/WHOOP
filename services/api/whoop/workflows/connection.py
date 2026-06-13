from __future__ import annotations

from urllib.parse import urlparse

from django.db import transaction

from users.services import ClearWhoopUserIdService, SetWhoopUserIdService
from whoop.exceptions import WhoopAuthError
from whoop.storage.connection_repository import WhoopConnectionRepository
from whoop.storage.oauth_state_repository import WhoopOAuthStateRepository
from whoop.whoop_api.auth_service import AuthService
from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.user_service import UserService


class BuildWhoopConnectUrlService:
    def __init__(
        self,
        *,
        auth_service: AuthService,
        oauth_state_repository: WhoopOAuthStateRepository,
        oauth_state_ttl_seconds: int,
        allowed_frontend_origins: set[str],
    ) -> None:
        self.auth_service = auth_service
        self.oauth_state_repository = oauth_state_repository
        self.oauth_state_ttl_seconds = oauth_state_ttl_seconds
        self.allowed_frontend_origins = allowed_frontend_origins

    def execute(self, *, user_id: str, frontend_success_url: str) -> dict[str, str]:
        validated_frontend_success_url = validate_frontend_success_url(
            frontend_success_url,
            allowed_origins=self.allowed_frontend_origins,
        )
        mapping = self.oauth_state_repository.create(
            user_id=user_id,
            frontend_success_url=validated_frontend_success_url,
            ttl_seconds=self.oauth_state_ttl_seconds,
        )
        return {
            "state": mapping.state,
            "connect_url": self.auth_service.build_authorization_url(
                state=mapping.state
            ),
        }


class CompleteWhoopConnectionService:
    def __init__(
        self,
        *,
        auth_service: AuthService,
        connection_repository: WhoopConnectionRepository,
        oauth_state_repository: WhoopOAuthStateRepository,
    ) -> None:
        self.auth_service = auth_service
        self.connection_repository = connection_repository
        self.oauth_state_repository = oauth_state_repository

    @transaction.atomic
    def execute(self, *, state: str, code: str):
        mapping = self.oauth_state_repository.consume(state=state)
        if mapping is None:
            raise ValueError("Invalid or expired WHOOP OAuth state.")

        token = self.auth_service.exchange_code(code)
        profile = UserService(
            BaseWhoopClient(access_token=token.access_token)
        ).get_basic_profile()
        self.connection_repository.save_connection(
            user_id=mapping.user_id,
            whoop_user_id=profile.user_id,
            token=token,
        )
        SetWhoopUserIdService().execute(
            user_id=mapping.user_id, whoop_user_id=profile.user_id
        )
        return mapping


class DisconnectWhoopService:
    def __init__(
        self,
        *,
        auth_service: AuthService,
        connection_repository: WhoopConnectionRepository,
    ) -> None:
        self.auth_service = auth_service
        self.connection_repository = connection_repository

    def execute(self, user_id: str) -> bool:
        connection = self.connection_repository.get_active_for_user(user_id)
        if connection is None:
            return False
        token = self.connection_repository.get_tokens(connection)
        try:
            self.auth_service.revoke_user_access(token.access_token)
        except WhoopAuthError:
            # Treat invalid/expired upstream access tokens as already disconnected.
            pass
        self.connection_repository.mark_revoked(connection)
        ClearWhoopUserIdService().execute(user_id=user_id)
        return True


def validate_frontend_success_url(
    frontend_success_url: str,
    *,
    allowed_origins: set[str],
) -> str:
    if not frontend_success_url:
        raise ValueError("Missing frontend success URL.")

    parsed = urlparse(frontend_success_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Frontend success URL must be an absolute http or https URL.")

    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in allowed_origins:
        raise ValueError("Frontend success URL origin is not allowed.")

    return frontend_success_url
