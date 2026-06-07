from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


@dataclass(frozen=True, slots=True)
class AuthSession:
    user: Any
    access: str
    refresh: str


class RegisterUserService:
    def execute(
        self, *, email: str, password: str, display_name: str = ""
    ) -> AuthSession:
        User = get_user_model()
        try:
            user = cast(Any, User.objects).create_user(
                email=email,
                password=password,
                display_name=display_name,
            )
        except IntegrityError as exc:
            raise ValueError("A user with this email already exists.") from exc

        return _session_for_user(user)


class AuthenticateUserService:
    def execute(self, *, email: str, password: str) -> AuthSession:
        user = authenticate(username=email, password=password)
        if user is None:
            raise ValueError("Invalid email or password.")
        if not user.is_active:
            raise ValueError("User account is inactive.")

        return _session_for_user(user)


class RefreshSessionService:
    def execute(self, *, refresh: str) -> dict[str, str]:
        serializer = TokenRefreshSerializer(data={"refresh": refresh})
        if serializer.is_valid():
            validated_data = cast(dict[str, Any], serializer.validated_data)
            return {str(key): str(value) for key, value in validated_data.items()}
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise ValueError("Refresh token is invalid or expired.") from exc
        raise ValueError("Refresh token is invalid or expired.")


class LogoutUserService:
    def execute(self, *, refresh: str) -> None:
        try:
            RefreshToken(cast(Any, refresh)).blacklist()
        except TokenError as exc:
            raise ValueError("Refresh token is invalid or expired.") from exc


def _session_for_user(user: Any) -> AuthSession:
    refresh = RefreshToken.for_user(user)
    return AuthSession(
        user=user, access=str(refresh.access_token), refresh=str(refresh)
    )
