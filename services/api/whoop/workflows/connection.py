from __future__ import annotations

from django.db import transaction

from users.services import SetWhoopUserIdService
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
    ) -> None:
        self.auth_service = auth_service
        self.oauth_state_repository = oauth_state_repository
        self.oauth_state_ttl_seconds = oauth_state_ttl_seconds

    def execute(self, *, user_id: str) -> dict[str, str]:
        mapping = self.oauth_state_repository.create(
            user_id=user_id,
            ttl_seconds=self.oauth_state_ttl_seconds,
        )
        return {
            "state": mapping.state,
            "connect_url": self.auth_service.build_authorization_url(state=mapping.state),
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
    def execute(self, *, state: str, code: str) -> str:
        mapping = self.oauth_state_repository.consume(state=state)
        if mapping is None:
            raise ValueError("Invalid or expired WHOOP OAuth state.")

        token = self.auth_service.exchange_code(code)
        profile = UserService(BaseWhoopClient(access_token=token.access_token)).get_basic_profile()
        self.connection_repository.save_connection(
            user_id=mapping.user_id,
            whoop_user_id=profile.user_id,
            token=token,
        )
        SetWhoopUserIdService().execute(user_id=mapping.user_id, whoop_user_id=profile.user_id)
        return mapping.user_id


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
        self.auth_service.revoke_user_access(token.access_token)
        self.connection_repository.mark_revoked(connection)
        return True
