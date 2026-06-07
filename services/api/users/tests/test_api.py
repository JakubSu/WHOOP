from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class UsersApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_register_returns_tokens_and_profile(self) -> None:
        response = self.client.post(
            reverse("user-register"),
            {
                "email": "athlete@example.com",
                "password": "strong-password",
                "display_name": "Athlete",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["email"], "athlete@example.com")
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_duplicate_email_is_rejected(self) -> None:
        User = get_user_model()
        cast(Any, User.objects).create_user(
            email="athlete@example.com", password="strong-password"
        )

        response = self.client.post(
            reverse("user-register"),
            {"email": "athlete@example.com", "password": "strong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_login_returns_tokens(self) -> None:
        User = get_user_model()
        cast(Any, User.objects).create_user(
            email="athlete@example.com", password="strong-password"
        )

        response = self.client.post(
            reverse("user-login"),
            {"email": "athlete@example.com", "password": "strong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_profile_requires_authentication(self) -> None:
        response = self.client.get(reverse("user-me"))

        self.assertEqual(response.status_code, 401)

    def test_profile_can_be_updated(self) -> None:
        User = get_user_model()
        user = cast(Any, User.objects).create_user(
            email="athlete@example.com", password="strong-password"
        )
        client = APIClient()
        client.force_authenticate(user)

        response = client.patch(
            reverse("user-me"),
            {"display_name": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["display_name"], "Updated")

    def test_refresh_rejects_blacklisted_token_with_400(self) -> None:
        register_response = self.client.post(
            reverse("user-register"),
            {
                "email": "athlete@example.com",
                "password": "strong-password",
            },
            format="json",
        )
        refresh_token = register_response.json()["refresh"]

        User = get_user_model()
        user = User.objects.get(email="athlete@example.com")
        client = APIClient()
        client.force_authenticate(user)
        logout_response = client.post(
            reverse("user-logout"),
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(logout_response.status_code, 204)

        refresh_response = self.client.post(
            reverse("user-token-refresh"),
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, 400)
        self.assertEqual(
            refresh_response.json()["detail"],
            "Refresh token is invalid or expired.",
        )
