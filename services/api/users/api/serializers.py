from django.conf import settings
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email address used to create and sign in to the account."
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Plaintext account password. Minimum length is 8 characters.",
    )
    display_name = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional display name shown in the application UI.",
    )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email address associated with the user account."
    )
    password = serializers.CharField(
        write_only=True, help_text="Plaintext account password."
    )


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional refresh token. If omitted, the API will also look for the HTTP-only refresh cookie.",
    )


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional refresh token to revoke. If omitted, the API will also look for the HTTP-only refresh cookie.",
    )


class ProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    display_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="User-facing display name that can be updated from the profile screen.",
    )
    whoop_user_id = serializers.CharField(
        read_only=True, help_text="WHOOP user identifier when the account is connected."
    )
    account_type = serializers.ChoiceField(choices=("normal", "demo"), read_only=True)
    whoop_connection_allowed = serializers.SerializerMethodField()
    expires_at = serializers.DateTimeField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_whoop_connection_allowed(self, user: object) -> bool:
        email = getattr(user, "email", "")
        return (
            getattr(user, "account_type", "") != "demo"
            and str(email).strip().lower() in settings.WHOOP_ALLOWED_USER_EMAILS
        )


class AuthSessionSerializer(serializers.Serializer):
    user = ProfileSerializer(read_only=True, help_text="Authenticated user profile.")
    access = serializers.CharField(
        read_only=True,
        help_text="Short-lived JWT access token for authenticated API calls.",
    )
    refresh = serializers.CharField(
        read_only=True,
        help_text="Long-lived JWT refresh token also mirrored to an HTTP-only cookie.",
    )


class DemoSessionSerializer(serializers.Serializer):
    user = ProfileSerializer(read_only=True)
    access = serializers.CharField(read_only=True)
