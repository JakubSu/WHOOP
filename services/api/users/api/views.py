from typing import Any, cast

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


class RegisterAPIView(APIView):
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

        return Response(
            AuthSessionSerializer(session).data, status=status.HTTP_201_CREATED
        )


class LoginAPIView(APIView):
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

        return Response(AuthSessionSerializer(session).data)


class RefreshAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        try:
            tokens = services.RefreshSessionService().execute(
                refresh=str(payload["refresh"])
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        return Response(tokens)


class LogoutAPIView(APIView):
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = _validated_data(serializer.validated_data)
        try:
            services.LogoutUserService().execute(refresh=str(payload["refresh"]))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc

        return Response(status=status.HTTP_204_NO_CONTENT)


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
