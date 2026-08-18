"""Monthly account and service-wide budget enforcement for Coach runs."""

from __future__ import annotations

import uuid
from datetime import UTC
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from coach.models import (
    CoachBudgetReservation,
    CoachGlobalMonthlyUsage,
    CoachUserMonthlyUsage,
)


class MonthlyBudgetExceeded(RuntimeError):
    """Raised when a new Coach run would exceed a monthly spending cap."""


def reserve_run_budget(*, user: Any, run_id: uuid.UUID) -> CoachBudgetReservation:
    """Reserve the maximum allowed cost for one run under both monthly caps."""

    reservation_amount = _money(settings.COACH_MAX_COST_USD)
    user_limit = _money(settings.COACH_USER_MONTHLY_BUDGET_USD)
    global_limit = _money(settings.COACH_GLOBAL_MONTHLY_BUDGET_USD)
    period_start = _current_period_start()

    with transaction.atomic():
        global_usage, _ = CoachGlobalMonthlyUsage.objects.get_or_create(
            period_start=period_start
        )
        global_usage = CoachGlobalMonthlyUsage.objects.select_for_update().get(
            pk=global_usage.pk
        )
        if _would_exceed(global_usage, global_limit, reservation_amount):
            raise MonthlyBudgetExceeded
        user_usage, _ = CoachUserMonthlyUsage.objects.get_or_create(
            user=user, period_start=period_start
        )
        user_usage = CoachUserMonthlyUsage.objects.select_for_update().get(
            pk=user_usage.pk
        )
        if _would_exceed(user_usage, user_limit, reservation_amount):
            raise MonthlyBudgetExceeded

        global_usage.reserved_usd += reservation_amount
        user_usage.reserved_usd += reservation_amount
        global_usage.save(update_fields=["reserved_usd", "updated_at"])
        user_usage.save(update_fields=["reserved_usd", "updated_at"])
        return CoachBudgetReservation.objects.create(
            run_id=run_id,
            user=user,
            user_monthly_usage=user_usage,
            global_monthly_usage=global_usage,
            reserved_usd=reservation_amount,
        )


def settle_run_budget(*, run_id: uuid.UUID, actual_cost_usd: Decimal) -> None:
    """Convert an in-flight reservation into the cost reported by the provider."""

    actual_cost = _money(actual_cost_usd)
    with transaction.atomic():
        reservation = _locked_reservation(run_id)
        if reservation.status != CoachBudgetReservation.Status.RESERVED:
            return
        _apply_finalization(
            reservation, actual_cost, CoachBudgetReservation.Status.SETTLED
        )


def release_run_budget(*, run_id: uuid.UUID) -> None:
    """Remove an unused reservation when no provider cost was incurred."""

    with transaction.atomic():
        reservation = _locked_reservation(run_id)
        if reservation.status != CoachBudgetReservation.Status.RESERVED:
            return
        _apply_finalization(
            reservation, Decimal(0), CoachBudgetReservation.Status.RELEASED
        )


def _locked_reservation(run_id: uuid.UUID) -> CoachBudgetReservation:
    reservation = CoachBudgetReservation.objects.select_for_update().get(run_id=run_id)
    reservation.global_monthly_usage = (
        CoachGlobalMonthlyUsage.objects.select_for_update().get(
            pk=reservation.global_monthly_usage_id
        )
    )
    reservation.user_monthly_usage = (
        CoachUserMonthlyUsage.objects.select_for_update().get(
            pk=reservation.user_monthly_usage_id
        )
    )
    return reservation


def _apply_finalization(
    reservation: CoachBudgetReservation, actual_cost: Decimal, status: str
) -> None:
    for usage in (reservation.global_monthly_usage, reservation.user_monthly_usage):
        usage.reserved_usd -= reservation.reserved_usd
        usage.spent_usd += actual_cost
        usage.save(update_fields=["reserved_usd", "spent_usd", "updated_at"])
    reservation.actual_usd = actual_cost
    reservation.status = status
    reservation.settled_at = timezone.now()
    reservation.save(update_fields=["actual_usd", "status", "settled_at"])


def _current_period_start():
    today = timezone.now().astimezone(UTC).date()
    return today.replace(day=1)


def _would_exceed(usage: Any, limit: Decimal, amount: Decimal) -> bool:
    return usage.spent_usd + usage.reserved_usd + amount > limit


def _money(value: object) -> Decimal:
    amount = Decimal(str(value))
    if amount < 0:
        raise ValueError("Budget amounts must not be negative.")
    return amount
