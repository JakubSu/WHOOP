from typing import Any, cast

from django.conf import settings
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

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


def _serializer_data(serializer: serializers.BaseSerializer[Any]) -> dict[str, Any]:
    return cast(dict[str, Any], serializer.data)


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
    )
    return response


def _refresh_from_request(request: Request, payload: dict[str, Any]) -> str:
    refresh = payload.get("refresh") or request.COOKIES.get(
        settings.JWT_REFRESH_COOKIE_NAME
    )
    if not refresh:
        raise ValidationError({"detail": "Refresh token is required."})
    return str(refresh)


ErrorDetailSerializer = inline_serializer(
    name="AuthErrorDetail",
    fields={"detail": serializers.CharField()},
)


RefreshTokenResponseSerializer = inline_serializer(
    name="RefreshTokenResponse",
    fields={
        "access": serializers.CharField(help_text="Fresh JWT access token."),
        "refresh": serializers.CharField(help_text="Rotated JWT refresh token."),
    },
)


class RegisterAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        description="Creates a new user account, returns an authenticated session, and sets the refresh token cookie.",
        request=RegisterSerializer,
        responses={
            201: AuthSessionSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Validation error."),
        },
        examples=[
            OpenApiExample(
                "Register request",
                request_only=True,
                value={
                    "email": "athlete@example.com",
                    "password": "StrongPassword123!",
                    "display_name": "Kuba",
                },
            ),
            OpenApiExample(
                "Register response",
                response_only=True,
                value={
                    "user": {
                        "id": "1e9fe7df-e59f-4c43-8228-7563fbb4f12e",
                        "email": "athlete@example.com",
                        "display_name": "Kuba",
                        "whoop_user_id": "",
                        "created_at": "2026-06-15T11:30:00Z",
                        "updated_at": "2026-06-15T11:30:00Z",
                    },
                    "access": "jwt-access-token",
                    "refresh": "jwt-refresh-token",
                },
            ),
        ],
    )
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

        data = _serializer_data(AuthSessionSerializer(session))
        return _set_refresh_cookie(
            Response(data, status=status.HTTP_201_CREATED),
            str(data.get("refresh", "")),
        )


class LoginAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Log in",
        description="Authenticates the user, returns an authenticated session, and sets the refresh token cookie.",
        request=LoginSerializer,
        responses={
            200: AuthSessionSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Invalid credentials or validation error."),
        },
        examples=[
            OpenApiExample(
                "Login request",
                request_only=True,
                value={"email": "athlete@example.com", "password": "StrongPassword123!"},
            ),
        ],
    )
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

        data = _serializer_data(AuthSessionSerializer(session))
        return _set_refresh_cookie(Response(data), str(data.get("refresh", "")))


class RefreshAPIView(APIView):
    authentication_classes: list[type[Any]] = []
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Refresh access token",
        description="Rotates the refresh token and returns a fresh access token pair. The refresh token may be provided in the request body or via the HTTP-only cookie.",
        request=RefreshSerializer,
        responses={
            200: RefreshTokenResponseSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Missing or invalid refresh token."),
        },
        examples=[
            OpenApiExample(
                "Refresh request",
                request_only=True,
                value={"refresh": "jwt-refresh-token"},
            ),
            OpenApiExample(
                "Refresh response",
                response_only=True,
                value={"access": "new-jwt-access-token", "refresh": "new-jwt-refresh-token"},
            ),
        ],
    )
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
    serializer_class = LogoutSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Log out",
        description="Revokes the refresh token and clears the refresh token cookie. The refresh token may be provided in the request body or via the HTTP-only cookie.",
        request=LogoutSerializer,
        responses={
            204: OpenApiResponse(description="Logout completed and refresh cookie cleared."),
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Missing or invalid refresh token."),
        },
        examples=[
            OpenApiExample(
                "Logout request",
                request_only=True,
                value={"refresh": "jwt-refresh-token"},
            ),
        ],
    )
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
    serializer_class = ProfileSerializer

    @extend_schema(
        tags=["Users"],
        summary="Get current user profile",
        description="Returns the authenticated user's profile, including WHOOP linkage metadata when available.",
        responses={
            200: ProfileSerializer,
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Profile not found."),
        },
    )
    def get(self, request: Request) -> Response:
        try:
            user = services.GetProfileService().execute(user_id=str(request.user.id))
        except ValueError as exc:
            raise NotFound(str(exc)) from exc

        return Response(ProfileSerializer(user).data)

    @extend_schema(
        tags=["Users"],
        summary="Update current user profile",
        description="Updates editable fields on the authenticated user's profile.",
        request=ProfileSerializer,
        responses={
            200: ProfileSerializer,
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Validation error."),
            404: OpenApiResponse(response=ErrorDetailSerializer, description="Profile not found."),
        },
        examples=[
            OpenApiExample(
                "Profile update request",
                request_only=True,
                value={"display_name": "Kuba Suran"},
            ),
        ],
    )
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
