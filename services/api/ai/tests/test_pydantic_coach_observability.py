from __future__ import annotations

from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from ai.implementations.pydantic_coach.observability import (
    configure_observability_from_settings,
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
