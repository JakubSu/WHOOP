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


def record_token_usage(
    *,
    run_id: object,
    context_input_tokens: int | None,
    raw_turn_count: int,
    visible_turn_count: int,
    dropped_turn_count: int,
    model_requests: list[dict[str, object]],
    model_input_tokens: int,
    model_output_tokens: int,
    request_count: int,
    tool_call_count: int,
    cost_usd: object,
) -> None:
    """Send a content-free token-budget event to Logfire for each run."""

    if not settings.COACH_LOGFIRE_ENABLED or not _configured:
        return
    try:
        import logfire

        logfire.info(
            "coach_token_usage",
            run_id=str(run_id),
            context_provider_input_tokens=context_input_tokens,
            context_raw_turn_count=raw_turn_count,
            context_visible_turn_count=visible_turn_count,
            context_dropped_turn_count=dropped_turn_count,
            model_requests=model_requests,
            input_provider_total_tokens=model_input_tokens,
            output_provider_total_tokens=model_output_tokens,
            request_count=request_count,
            tool_call_count=tool_call_count,
            cost_usd=str(cost_usd),
        )
    except Exception:
        logger.exception("coach_token_usage_logfire_failed run_id=%s", run_id)
