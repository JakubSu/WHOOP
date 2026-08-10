"""Pydantic AI implementation of the owned Coach runner contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .runner import PydanticCoachRunner

__all__ = ("PydanticCoachRunner", "create_pydantic_coach_runner")


def create_pydantic_coach_runner() -> Any:
    """Lazily load Django-bound runner code for the configured factory."""

    from .runner import create_pydantic_coach_runner as factory

    return factory()


def __getattr__(name: str) -> Any:
    if name == "PydanticCoachRunner":
        from .runner import PydanticCoachRunner

        return PydanticCoachRunner
    raise AttributeError(name)
