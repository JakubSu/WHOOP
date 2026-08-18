from __future__ import annotations

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class DemoAwareJWTAuthentication(JWTAuthentication):
    """Reject expired temporary accounts even if an access token remains valid."""

    def get_user(self, validated_token):  # type: ignore[no-untyped-def]
        user = super().get_user(validated_token)
        if getattr(user, "is_expired", False):
            raise AuthenticationFailed("This demo session has expired.", code="demo_expired")
        return user
