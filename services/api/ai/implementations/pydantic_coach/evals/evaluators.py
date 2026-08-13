"""Objective checks used by deterministic Coach evaluation scenarios."""

from __future__ import annotations

from typing import Any


def assert_case_matches(
    *,
    case: dict[str, Any],
    response: str,
    activity_kinds: set[str],
    recommendation_created: bool,
) -> None:
    """Fail with an actionable assertion when a required Coach behavior is absent."""

    if not response.strip():
        raise AssertionError(f"{case['name']}: response must not be empty.")
    missing_terms = [
        term
        for term in case.get("required_response_terms", [])
        if term.lower() not in response.lower()
    ]
    if missing_terms:
        raise AssertionError(
            f"{case['name']}: response is missing required guidance: {', '.join(missing_terms)}."
        )
    required_kind = case.get("required_activity_kind")
    if required_kind and required_kind not in activity_kinds:
        raise AssertionError(f"{case['name']}: missing {required_kind} activity.")
    if case.get("requires_recommendation") and not recommendation_created:
        raise AssertionError(f"{case['name']}: expected a recommendation proposal.")
    if case.get("forbids_recommendation") and recommendation_created:
        raise AssertionError(
            f"{case['name']}: recommendation proposal must not be created."
        )
