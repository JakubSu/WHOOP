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
                "email": "test-athlete@example.com",
                "password": "strong-password",
                "display_name": "Athlete",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["email"], "test-athlete@example.com")
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_duplicate_email_is_rejected(self) -> None:
        User = get_user_model()
        cast(Any, User.objects).create_user(
            email="test-athlete@example.com", password="strong-password"
        )

        response = self.client.post(
            reverse("user-register"),
            {"email": "test-athlete@example.com", "password": "strong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_login_returns_tokens(self) -> None:
        User = get_user_model()
        cast(Any, User.objects).create_user(
            email="test-athlete@example.com", password="strong-password"
        )

        response = self.client.post(
            reverse("user-login"),
            {"email": "test-athlete@example.com", "password": "strong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertIn("whoop_refresh", response.cookies)

    def test_login_ignores_stale_bearer_header_with_valid_credentials(self) -> None:
        User = get_user_model()
        cast(Any, User.objects).create_user(
            email="test-athlete@example.com", password="strong-password"
        )

        response = self.client.post(
            reverse("user-login"),
            {"email": "test-athlete@example.com", "password": "strong-password"},
            format="json",
            HTTP_AUTHORIZATION="Bearer stale-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())

    def test_profile_requires_authentication(self) -> None:
        response = self.client.get(reverse("user-me"))

        self.assertEqual(response.status_code, 401)

    def test_profile_can_be_updated(self) -> None:
        User = get_user_model()
        user = cast(Any, User.objects).create_user(
            email="test-athlete@example.com", password="strong-password"
        )
        client = APIClient()
        client.force_authenticate(user)

        response = cast(
            Any,
            client.patch(
                reverse("user-me"),
                {"display_name": "Updated"},
                format="json",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["display_name"], "Updated")

    def test_refresh_rejects_blacklisted_token_with_400(self) -> None:
        register_response = self.client.post(
            reverse("user-register"),
            {
                "email": "test-athlete@example.com",
                "password": "strong-password",
            },
            format="json",
        )
        refresh_token = register_response.json()["refresh"]

        User = get_user_model()
        user = User.objects.get(email="test-athlete@example.com")
        client = APIClient()
        client.force_authenticate(user)
        logout_response = cast(
            Any,
            client.post(
                reverse("user-logout"),
                {"refresh": refresh_token},
                format="json",
            ),
        )
        self.assertEqual(logout_response.status_code, 204)

        refresh_response = cast(
            Any,
            self.client.post(
                reverse("user-token-refresh"),
                {"refresh": refresh_token},
                format="json",
            ),
        )

        self.assertEqual(refresh_response.status_code, 400)
        self.assertEqual(
            refresh_response.json()["detail"],
            "Refresh token is invalid or expired.",
        )

    def test_refresh_accepts_refresh_cookie(self) -> None:
        register_response = self.client.post(
            reverse("user-register"),
            {
                "email": "cookie-refresh@example.com",
                "password": "strong-password",
            },
            format="json",
        )
        self.assertIn("whoop_refresh", register_response.cookies)

        response = self.client.post(
            reverse("user-token-refresh"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertIn("whoop_refresh", response.cookies)

    def test_logout_accepts_valid_refresh_without_access_token(self) -> None:
        register_response = self.client.post(
            reverse("user-register"),
            {
                "email": "logout-no-access@example.com",
                "password": "strong-password",
            },
            format="json",
        )
        refresh_token = register_response.json()["refresh"]

        response = self.client.post(
            reverse("user-logout"),
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, 204)

    def test_logout_accepts_refresh_cookie_and_clears_it(self) -> None:
        register_response = self.client.post(
            reverse("user-register"),
            {
                "email": "logout-cookie@example.com",
                "password": "strong-password",
            },
            format="json",
        )
        self.assertIn("whoop_refresh", register_response.cookies)

        response = self.client.post(reverse("user-logout"), {}, format="json")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies["whoop_refresh"].value, "")

    def test_logout_ignores_stale_bearer_header_with_valid_refresh(self) -> None:
        register_response = self.client.post(
            reverse("user-register"),
            {
                "email": "logout-stale-header@example.com",
                "password": "strong-password",
            },
            format="json",
        )
        refresh_token = register_response.json()["refresh"]

        response = self.client.post(
            reverse("user-logout"),
            {"refresh": refresh_token},
            format="json",
            HTTP_AUTHORIZATION="Bearer stale-token",
        )

        self.assertEqual(response.status_code, 204)
