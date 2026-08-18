from __future__ import annotations

from decimal import Decimal
from typing import Any, cast
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from coach.budget import (
    MonthlyBudgetExceeded,
    release_run_budget,
    reserve_run_budget,
    settle_run_budget,
)
from coach.models import (
    CoachBudgetReservation,
    CoachGlobalMonthlyUsage,
    CoachUserMonthlyUsage,
)


@override_settings(
    COACH_MAX_COST_USD=Decimal("0.05"),
    COACH_USER_MONTHLY_BUDGET_USD=Decimal("0.10"),
    COACH_GLOBAL_MONTHLY_BUDGET_USD=Decimal("0.15"),
)
class CoachBudgetTests(TestCase):
    def setUp(self) -> None:
        user_model = cast(Any, get_user_model())
        self.user = user_model.objects.create_user(
            email="budget@example.com", password="strong-password"
        )

    def test_settling_a_run_replaces_its_reservation_with_actual_cost(self) -> None:
        reservation = reserve_run_budget(user=self.user, run_id=uuid4())

        self.assertEqual(reservation.reserved_usd, Decimal("0.05"))
        settle_run_budget(run_id=reservation.run_id, actual_cost_usd=Decimal("0.03"))

        user_usage = CoachUserMonthlyUsage.objects.get(user=self.user)
        global_usage = CoachGlobalMonthlyUsage.objects.get()
        reservation.refresh_from_db()
        self.assertEqual(user_usage.reserved_usd, Decimal(0))
        self.assertEqual(user_usage.spent_usd, Decimal("0.03"))
        self.assertEqual(global_usage.reserved_usd, Decimal(0))
        self.assertEqual(global_usage.spent_usd, Decimal("0.03"))
        self.assertEqual(reservation.status, CoachBudgetReservation.Status.SETTLED)
        self.assertEqual(reservation.actual_usd, Decimal("0.03"))

    def test_user_cap_rejects_a_new_reservation_without_changing_usage(self) -> None:
        first = reserve_run_budget(user=self.user, run_id=uuid4())
        settle_run_budget(run_id=first.run_id, actual_cost_usd=Decimal("0.10"))

        with self.assertRaises(MonthlyBudgetExceeded):
            reserve_run_budget(user=self.user, run_id=uuid4())

        usage = CoachUserMonthlyUsage.objects.get(user=self.user)
        self.assertEqual(usage.spent_usd, Decimal("0.10"))
        self.assertEqual(usage.reserved_usd, Decimal(0))

    def test_global_cap_rejects_a_different_user(self) -> None:
        first = reserve_run_budget(user=self.user, run_id=uuid4())
        settle_run_budget(run_id=first.run_id, actual_cost_usd=Decimal("0.15"))
        user_model = cast(Any, get_user_model())
        other_user = user_model.objects.create_user(
            email="other-budget@example.com", password="strong-password"
        )

        with self.assertRaises(MonthlyBudgetExceeded):
            reserve_run_budget(user=other_user, run_id=uuid4())

        self.assertFalse(CoachUserMonthlyUsage.objects.filter(user=other_user).exists())

    def test_releasing_a_run_removes_its_reservation_without_charging_it(self) -> None:
        reservation = reserve_run_budget(user=self.user, run_id=uuid4())

        release_run_budget(run_id=reservation.run_id)

        reservation.refresh_from_db()
        user_usage = CoachUserMonthlyUsage.objects.get(user=self.user)
        self.assertEqual(reservation.status, CoachBudgetReservation.Status.RELEASED)
        self.assertEqual(user_usage.reserved_usd, Decimal(0))
        self.assertEqual(user_usage.spent_usd, Decimal(0))

    @override_settings(COACH_DEMO_TOTAL_BUDGET_USD=Decimal("0.03"), COACH_DEMO_MAX_COST_USD=Decimal("0.005"))
    def test_demo_user_uses_demo_budget_and_six_request_reservations(self) -> None:
        user_model = cast(Any, get_user_model())
        demo = user_model.objects.create_user(
            email="demo@example.invalid",
            password="strong-password",
            account_type="demo",
        )

        reservations = [reserve_run_budget(user=demo, run_id=uuid4()) for _ in range(6)]

        self.assertTrue(all(item.reserved_usd == Decimal("0.005") for item in reservations))
        with self.assertRaises(MonthlyBudgetExceeded):
            reserve_run_budget(user=demo, run_id=uuid4())
