from __future__ import annotations

from django.conf import settings

from whoop.storage.connection_repository import WhoopConnectionRepository
from whoop.storage.oauth_state_repository import WhoopOAuthStateRepository
from whoop.storage.snapshot_repository import WhoopSnapshotRepository
from whoop.storage.token_crypto import TokenCrypto
from whoop.whoop_api.auth_service import AuthService
from whoop.whoop_api.base_client import BaseWhoopClient
from whoop.whoop_api.cycle_service import CycleService
from whoop.whoop_api.recovery_service import RecoveryService
from whoop.whoop_api.sleep_service import SleepService
from whoop.whoop_api.workout_service import WorkoutService
from whoop.workflows.connection import (
    BuildWhoopConnectUrlService,
    CompleteWhoopConnectionService,
    DisconnectWhoopService,
)
from whoop.workflows.summary import GetWhoopSummaryService, WhoopApiServices


def create_auth_service() -> AuthService:
    return AuthService(
        client=BaseWhoopClient(),
        client_id=settings.WHOOP_CLIENT_ID,
        client_secret=settings.WHOOP_CLIENT_SECRET,
        redirect_uri=settings.WHOOP_REDIRECT_URI,
        scopes=settings.WHOOP_SCOPES,
    )


def create_connection_repository() -> WhoopConnectionRepository:
    return WhoopConnectionRepository(TokenCrypto())


def create_snapshot_repository() -> WhoopSnapshotRepository:
    return WhoopSnapshotRepository()


def create_oauth_state_repository() -> WhoopOAuthStateRepository:
    return WhoopOAuthStateRepository()


def create_api_services(access_token: str) -> WhoopApiServices:
    client = BaseWhoopClient(access_token=access_token)
    return WhoopApiServices(
        cycle_service=CycleService(client),
        recovery_service=RecoveryService(client),
        sleep_service=SleepService(client),
        workout_service=WorkoutService(client),
    )


def create_build_connect_url_service() -> BuildWhoopConnectUrlService:
    return BuildWhoopConnectUrlService(
        auth_service=create_auth_service(),
        oauth_state_repository=create_oauth_state_repository(),
        oauth_state_ttl_seconds=settings.WHOOP_OAUTH_STATE_TTL_SECONDS,
        allowed_frontend_origins=set(settings.WHOOP_FRONTEND_ALLOWED_ORIGINS),
    )


def create_complete_connection_service() -> CompleteWhoopConnectionService:
    return CompleteWhoopConnectionService(
        auth_service=create_auth_service(),
        connection_repository=create_connection_repository(),
        oauth_state_repository=create_oauth_state_repository(),
    )


def create_disconnect_service() -> DisconnectWhoopService:
    return DisconnectWhoopService(
        auth_service=create_auth_service(),
        connection_repository=create_connection_repository(),
    )


def create_summary_service() -> GetWhoopSummaryService:
    return GetWhoopSummaryService(
        connection_repository=create_connection_repository(),
        snapshot_repository=create_snapshot_repository(),
        auth_service=create_auth_service(),
        api_services_factory=create_api_services,
    )
