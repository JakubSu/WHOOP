from __future__ import annotations

from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from ai.implementations.pydantic_coach.observability import (
    configure_observability_from_settings,
    record_token_usage,
)


class PydanticCoachObservabilityTests(SimpleTestCase):
    @override_settings(
        COACH_LOGFIRE_ENABLED=True,
        LOGFIRE_SERVICE_NAME="whoop-coach-test",
        COACH_LOGFIRE_CAPTURE_CONTENT=True,
        COACH_LOGFIRE_CAPTURE_BINARY_CONTENT=False,
        COACH_LOGFIRE_CAPTURE_MODEL_REQUEST_PARAMETERS=True,
    )
    @patch("ai.implementations.pydantic_coach.observability.configure_observability")
    def test_configuration_uses_django_settings(
        self, configure_observability: Mock
    ) -> None:
        configure_observability_from_settings()

        configure_observability.assert_called_once_with(
            enabled=True,
            service_name="whoop-coach-test",
            capture_content=True,
            capture_binary_content=False,
            capture_model_request_parameters=True,
        )

    @override_settings(COACH_LOGFIRE_ENABLED=True)
    @patch("ai.implementations.pydantic_coach.observability.logger")
    def test_token_usage_is_sent_to_logfire_without_content(self, logger: Mock) -> None:
        logfire = Mock()
        with (
            patch.dict("sys.modules", {"logfire": logfire}),
            patch("ai.implementations.pydantic_coach.observability._configured", True),
        ):
            record_token_usage(
                run_id="run-1",
                context_input_tokens=8_000,
                raw_turn_count=1,
                visible_turn_count=0,
                dropped_turn_count=2,
                model_requests=[
                    {
                        "number": 1,
                        "input_tokens": 8_000,
                        "output_tokens": 300,
                        "cached_tokens": 0,
                        "details": {"reasoning_tokens": 200},
                    }
                ],
                model_input_tokens=8_000,
                model_output_tokens=300,
                request_count=2,
                tool_call_count=1,
                cost_usd="0.01",
            )

        logfire.info.assert_called_once_with(
            "coach_token_usage",
            run_id="run-1",
            context_provider_input_tokens=8_000,
            context_raw_turn_count=1,
            context_visible_turn_count=0,
            context_dropped_turn_count=2,
            model_requests=[
                {
                    "number": 1,
                    "input_tokens": 8_000,
                    "output_tokens": 300,
                    "cached_tokens": 0,
                    "details": {"reasoning_tokens": 200},
                }
            ],
            input_provider_total_tokens=8_000,
            output_provider_total_tokens=300,
            request_count=2,
            tool_call_count=1,
            cost_usd="0.01",
        )
        logger.exception.assert_not_called()
