"""Objective checks used by deterministic Coach evaluation scenarios."""

from __future__ import annotations

from typing import Any

from ..contracts import CoachResponse


def assert_case_matches(
    *,
    case: dict[str, Any],
    response: CoachResponse,
    activity_kinds: set[str],
    recommendation_created: bool,
) -> None:
    """Fail with an actionable assertion when a required Coach behavior is absent."""

    if response.outcome != case["expected_outcome"]:
        raise AssertionError(
            f"{case['name']}: expected {case['expected_outcome']}, got {response.outcome}."
        )
    required_kind = case.get("required_activity_kind")
    if required_kind and required_kind not in activity_kinds:
        raise AssertionError(f"{case['name']}: missing {required_kind} activity.")
    if case.get("requires_recommendation") and not recommendation_created:
        raise AssertionError(f"{case['name']}: expected a recommendation proposal.")
    if case.get("forbids_recommendation") and recommendation_created:
        raise AssertionError(f"{case['name']}: recommendation proposal must not be created.")
