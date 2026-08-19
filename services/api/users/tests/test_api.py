from typing import Any, cast

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from coach.models import CoachConversation, CoachMessage, UiAction
from recommendation.models import Recommendation, RecommendationOperation
from training.models import Exercise, Workout, WorkoutExercise
from whoop.models import WhoopSnapshot


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

    @override_settings(WHOOP_TOKEN_ENCRYPTION_KEY=Fernet.generate_key().decode())
    def test_demo_session_creates_isolated_seeded_workspace_without_refresh(self) -> None:
        response = self.client.post(reverse("user-demo-session"), {}, format="json")

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn("access", body)
        self.assertNotIn("refresh", body)
        self.assertNotIn("whoop_refresh", response.cookies)
        self.assertEqual(body["user"]["account_type"], "demo")
        self.assertIsNotNone(body["user"]["expires_at"])

        user = get_user_model().objects.get(pk=body["user"]["id"])
        self.assertEqual(Exercise.objects.filter(user_id=str(user.id)).count(), 0)
        workout = Workout.objects.get(user_id=str(user.id))
        self.assertEqual(workout.name, "Lower Body Strength")
        self.assertEqual(workout.date, timezone.localdate(user.created_at))
        self.assertEqual(
            list(
                WorkoutExercise.objects.filter(workout=workout)
                .order_by("sort_order")
                .values_list("exercise__name", flat=True)
            ),
            ["Back Squat", "Deadlift", "Bulgarian Split Squat", "Hamstring Curl"],
        )
        snapshot = WhoopSnapshot.objects.get(user_id=str(user.id))
        self.assertEqual(snapshot.created_at, user.created_at)

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access']}")
        summary = client.get(reverse("whoop-summary"))
        self.assertEqual(summary.status_code, 200)
        self.assertTrue(summary.json()["connected"])
        self.assertEqual(summary.json()["recovery_score"], 78.0)

    def test_expired_demo_access_token_is_rejected(self) -> None:
        response = self.client.post(reverse("user-demo-session"), {}, format="json")
        user = get_user_model().objects.get(pk=response.json()["user"]["id"])
        user.expires_at = timezone.now()
        user.save(update_fields=["expires_at"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
        self.assertEqual(self.client.get(reverse("user-me")).status_code, 401)

    def test_purge_expired_demo_users_removes_coach_and_recommendation_data(self) -> None:
        User = get_user_model()
        demo_user = User.objects.create_user(
            email="expired-demo@example.com",
            account_type=User.AccountType.DEMO,
            expires_at=timezone.now(),
        )
        conversation = CoachConversation.objects.create(user=demo_user)
        message = CoachMessage.objects.create(
            conversation=conversation,
            role=CoachMessage.Role.ASSISTANT,
            content="Demo advice",
        )
        UiAction.objects.create(message=message, type="test", payload={})
        recommendation = Recommendation.objects.create(
            user=demo_user,
            conversation=conversation,
            coach_message=message,
            summary="Demo recommendation",
        )
        RecommendationOperation.objects.create(
            recommendation=recommendation,
            operation_type=RecommendationOperation.OperationType.ADD_WORKOUT,
            payload={},
        )

        call_command("purge_expired_demo_users")

        self.assertFalse(User.objects.filter(pk=demo_user.pk).exists())
        self.assertFalse(CoachConversation.objects.filter(pk=conversation.pk).exists())
        self.assertFalse(CoachMessage.objects.filter(pk=message.pk).exists())
        self.assertFalse(UiAction.objects.exists())
        self.assertFalse(Recommendation.objects.filter(pk=recommendation.pk).exists())
        self.assertFalse(RecommendationOperation.objects.exists())

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
