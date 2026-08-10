"""Privacy-preserving observability for the Pydantic Coach implementation."""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)
_configured = False
_lock = threading.Lock()


def configure_observability(*, enabled: bool, service_name: str) -> None:
    """Configure Pydantic AI instrumentation once without content capture."""

    global _configured
    if not enabled:
        return
    with _lock:
        if _configured:
            return
        try:
            import logfire
            from pydantic_ai import Agent
            from pydantic_ai.agent import InstrumentationSettings

            logfire.configure(service_name=service_name)
            Agent.instrument_all(
                InstrumentationSettings(
                    include_binary_content=False,
                    include_content=False,
                    include_model_request_parameters=False,
                )
            )
        except Exception:
            logger.exception("coach_observability_configuration_failed")
            raise
        _configured = True
