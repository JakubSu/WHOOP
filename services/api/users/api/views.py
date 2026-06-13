from typing import Any, cast

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from users import services
from users.api.serializers import (
    AuthSessionSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    RefreshSerializer,
    RegisterSerializer,
)


def _validated_data(data: Any) -> dict[str, Any]:
    return cast(dict[str, Any], data)


def _refresh_cookie_max_age() -> int:
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    return int(lifetime.total_seconds())


def _set_refresh_cookie(response: Response, refresh: str | None) -> Response:
    if not refresh:
        return response

    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        refresh,
        max_age=_refresh_cookie_max_age(),
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        path="/api/v1/users/",
    )
    return response


def _clear_refresh_cookie(response: Response) -> Response:
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        path="/api/v1/users/",
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )
    return response


def _refresh_from_request(request: Request, payload: dict[str, Any]) -> str:
    refresh = payload.get("refresh") or request.COOKIES.get(
        settings.JWT_REFRESH_COOKIE_NAME
    )
    if not refresh:
        raise ValidationError({"detail": "Refresh token is required."})
    return str(refresh)


class RegisterAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        try:
            session = services.RegisterUserService().execute(
                email=str(payload["email"]),
                password=str(payload["password"]),
                display_name=str(payload.get("display_name", "")),
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        data = AuthSessionSerializer(session).data
        return _set_refresh_cookie(
            Response(data, status=status.HTTP_201_CREATED),
            str(data.get("refresh", "")),
        )


class LoginAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        try:
            session = services.AuthenticateUserService().execute(
                email=str(payload["email"]),
                password=str(payload["password"]),
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        data = AuthSessionSerializer(session).data
        return _set_refresh_cookie(Response(data), str(data.get("refresh", "")))


class RefreshAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        try:
            tokens = services.RefreshSessionService().execute(
                refresh=_refresh_from_request(request, payload)
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        return _set_refresh_cookie(Response(tokens), tokens.get("refresh"))


class LogoutAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        try:
            services.LogoutUserService().execute(
                refresh=_refresh_from_request(request, payload)
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        return _clear_refresh_cookie(Response(status=status.HTTP_204_NO_CONTENT))


class CurrentUserProfileAPIView(APIView):
    def get(self, request: Request) -> Response:
        try:
            user = services.GetProfileService().execute(user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc

        return Response(ProfileSerializer(user).data)

    def patch(self, request: Request) -> Response:
        serializer = ProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        display_name = payload.get("display_name")
        try:
            user = services.UpdateProfileService().execute(
                user_id=str(request.user.id),
                display_name=str(display_name) if display_name is not None else None,
            )
        except ValueError as exc:
            raise NotFound(str(exc)) from exc

        return Response(ProfileSerializer(user).data)
