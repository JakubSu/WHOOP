"""Privacy-preserving observability for the Pydantic Coach implementation."""

from __future__ import annotations

import logging
import threading

from django.conf import settings

logger = logging.getLogger(__name__)
_configured = False
_lock = threading.Lock()


def configure_observability(
    *,
    enabled: bool,
    service_name: str,
    capture_content: bool,
    capture_binary_content: bool,
    capture_model_request_parameters: bool,
) -> None:
    """Configure Pydantic AI instrumentation once using explicit privacy controls."""

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
                    include_binary_content=capture_binary_content,
                    include_content=capture_content,
                    include_model_request_parameters=capture_model_request_parameters,
                )
            )
        except Exception:
            logger.exception("coach_observability_configuration_failed")
            raise
        _configured = True


def configure_observability_from_settings() -> None:
    """Configure Coach tracing while an ASGI worker starts."""

    configure_observability(
        enabled=bool(settings.COACH_LOGFIRE_ENABLED),
        service_name=str(settings.LOGFIRE_SERVICE_NAME),
        capture_content=bool(settings.COACH_LOGFIRE_CAPTURE_CONTENT),
        capture_binary_content=bool(settings.COACH_LOGFIRE_CAPTURE_BINARY_CONTENT),
        capture_model_request_parameters=bool(
            settings.COACH_LOGFIRE_CAPTURE_MODEL_REQUEST_PARAMETERS
        ),
    )
