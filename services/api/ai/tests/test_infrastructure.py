from types import SimpleNamespace
from typing import cast

from django.test import SimpleTestCase, override_settings
from pydantic import BaseModel

from ai.infrastructure.exceptions import (
    AIProviderConfigurationError,
    AIProviderRateLimitError,
    AIProviderRequestError,
    AIProviderResponseValidationError,
    AIProviderTimeoutError,
    PromptNotFoundError,
)
from ai.infrastructure.models import LLMRequestMetadata
from ai.infrastructure.prompt_loader import FileSystemPromptLoader
from ai.infrastructure.providers.openai_provider import OpenAIProvider
from ai.infrastructure.services import get_llm_provider
from ai.infrastructure.structured_response_parser import (
    PydanticStructuredResponseParser,
)


class ExampleResponse(BaseModel):
    title: str
    score: int


class FakeResponses:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def parse(self, **kwargs):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeClient:
    def __init__(self, responses):
        self.responses = FakeResponses(responses)


class FakeOpenAIBadRequest(Exception):
    status_code = 400
    body = {
        "error": {
            "type": "invalid_request_error",
            "code": "invalid_json_schema",
            "param": "text.format.schema",
            "message": "Invalid schema for response_format.",
        }
    }


class AIInfrastructureTests(SimpleTestCase):
    def test_prompt_loader_loads_prompt_by_namespace_name_and_version(self):
        loader = FileSystemPromptLoader()

        prompt = loader.load(
            namespace="recommendation",
            name="test_prompt",
            version="v1",
        )

        self.assertEqual(prompt.namespace, "recommendation")
        self.assertEqual(prompt.name, "test_prompt")
        self.assertEqual(prompt.version, "v1")
        self.assertIn("{input}", prompt.template)

    def test_prompt_loader_raises_for_missing_prompt(self):
        loader = FileSystemPromptLoader()

        with self.assertRaises(PromptNotFoundError):
            loader.load(namespace="recommendation", name="missing", version="v1")

    def test_prompt_loader_renders_minimal_template_values(self):
        loader = FileSystemPromptLoader()
        prompt = loader.load(
            namespace="recommendation",
            name="test_prompt",
            version="v1",
        )

        rendered = loader.render(prompt, {"input": "hello"})

        self.assertIn("hello", rendered)

    def test_structured_parser_validates_json_string(self):
        parser = PydanticStructuredResponseParser()

        parsed = cast(
            ExampleResponse,
            parser.parse(
                raw_response='{"title": "Plan", "score": 9}',
                response_model=ExampleResponse,
            ),
        )

        self.assertEqual(parsed.title, "Plan")
        self.assertEqual(parsed.score, 9)

    def test_structured_parser_validates_dict(self):
        parser = PydanticStructuredResponseParser()

        parsed = cast(
            ExampleResponse,
            parser.parse(
                raw_response={"title": "Plan", "score": 9},
                response_model=ExampleResponse,
            ),
        )

        self.assertEqual(parsed.title, "Plan")

    def test_structured_parser_rejects_malformed_json(self):
        parser = PydanticStructuredResponseParser()

        with self.assertRaises(AIProviderResponseValidationError):
            parser.parse(raw_response="{", response_model=ExampleResponse)

    def test_structured_parser_rejects_schema_invalid_json(self):
        parser = PydanticStructuredResponseParser()

        with self.assertRaises(AIProviderResponseValidationError):
            parser.parse(
                raw_response='{"title": "Plan"}',
                response_model=ExampleResponse,
            )

    def test_openai_provider_returns_typed_response_from_mocked_client(self):
        response = SimpleNamespace(
            output_parsed=ExampleResponse(title="Plan", score=10),
            usage=SimpleNamespace(input_tokens=11, output_tokens=7, total_tokens=18),
        )
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([response]),
        )

        result = provider.generate_structured(
            prompt="Return JSON.",
            input_data={"input": "hello"},
            response_model=ExampleResponse,
            metadata=LLMRequestMetadata(
                prompt_namespace="recommendation",
                prompt_name="test_prompt",
                prompt_version="v1",
            ),
        )

        self.assertIsInstance(result, ExampleResponse)
        self.assertEqual(result.score, 10)

    def test_openai_provider_retries_transient_failures(self):
        response = SimpleNamespace(
            output_parsed={"title": "Plan", "score": 8},
            usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
        )
        client = FakeClient([RuntimeError("temporary server error"), response])
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=client,
            max_retries=1,
        )

        result = provider.generate_structured(
            prompt="Return JSON.",
            input_data={},
            response_model=ExampleResponse,
        )

        self.assertEqual(result.score, 8)
        self.assertEqual(client.responses.calls, 2)

    def test_openai_provider_maps_timeout(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([TimeoutError("timeout")]),
            max_retries=0,
        )

        with self.assertRaises(AIProviderTimeoutError):
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
            )

    def test_openai_provider_maps_rate_limit(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([RuntimeError("rate limit exceeded")]),
            max_retries=0,
        )

        with self.assertRaises(AIProviderRateLimitError):
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
            )

    def test_openai_provider_does_not_retry_bad_request_and_preserves_details(self):
        client = FakeClient([FakeOpenAIBadRequest("bad request")])
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=client,
            max_retries=2,
        )

        with self.assertRaisesRegex(
            AIProviderRequestError,
            "status_code=400.*code=invalid_json_schema.*param=text.format.schema",
        ):
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
            )

        self.assertEqual(client.responses.calls, 1)

    def test_openai_provider_maps_invalid_response(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([SimpleNamespace(output_text='{"title": "Plan"}')]),
            max_retries=0,
        )

        with self.assertRaises(AIProviderResponseValidationError):
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
            )

    @override_settings(AI_LLM_PROVIDER="openai", OPENAI_API_KEY="test-key")
    def test_provider_factory_returns_openai_provider(self):
        provider = get_llm_provider()

        self.assertIsInstance(provider, OpenAIProvider)

    @override_settings(AI_LLM_PROVIDER="unknown")
    def test_provider_factory_rejects_unknown_provider(self):
        with self.assertRaises(AIProviderConfigurationError):
            get_llm_provider()

    def test_observability_logging_includes_metadata_and_usage(self):
        response = SimpleNamespace(
            output_parsed=ExampleResponse(title="Plan", score=10),
            usage=SimpleNamespace(input_tokens=11, output_tokens=7, total_tokens=18),
        )
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([response]),
        )

        with self.assertLogs(
            "ai.infrastructure.providers.openai_provider",
            level="INFO",
        ) as logs:
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
                metadata=LLMRequestMetadata(
                    prompt_namespace="recommendation",
                    prompt_name="test_prompt",
                    prompt_version="v1",
                ),
            )

        output = "\n".join(logs.output)
        self.assertIn('"model": "test-model"', output)
        self.assertIn('"prompt_length": 12', output)
        self.assertIn('"response_length": 27', output)
        self.assertIn('"prompt_version": "v1"', output)
        self.assertIn('"input_tokens": 11', output)
        self.assertIn('"status": "success"', output)
        self.assertNotIn('"prompt": "Return JSON."', output)

    @override_settings(LOG_LLM_PAYLOADS=True)
    def test_observability_logging_can_include_payloads_when_enabled(self):
        response = SimpleNamespace(
            output_parsed=ExampleResponse(title="Plan", score=10),
            usage=SimpleNamespace(input_tokens=11, output_tokens=7, total_tokens=18),
        )
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([response]),
        )

        with self.assertLogs(
            "ai.infrastructure.providers.openai_provider",
            level="INFO",
        ) as logs:
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
                metadata=LLMRequestMetadata(
                    prompt_namespace="recommendation",
                    prompt_name="test_prompt",
                    prompt_version="v1",
                ),
            )

        output = "\n".join(logs.output)
        self.assertIn('"prompt": "Return JSON."', output)
        self.assertIn('"response": "{\\"score\\":10,\\"title\\":\\"Plan\\"}"', output)

    def test_observability_logging_includes_prompt_on_failure(self):
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            client=FakeClient([RuntimeError("temporary server error")]),
            max_retries=0,
        )

        with self.assertLogs(
            "ai.infrastructure.providers.openai_provider",
            level="INFO",
        ) as logs:
            with self.assertRaises(AIProviderRequestError):
                provider.generate_structured(
                    prompt="Return JSON.",
                    input_data={},
                    response_model=ExampleResponse,
                    metadata=LLMRequestMetadata(
                        prompt_namespace="recommendation",
                        prompt_name="test_prompt",
                        prompt_version="v1",
                    ),
                )

        output = "\n".join(logs.output)
        self.assertIn('"prompt_length": 12', output)
        self.assertIn('"response_length": 0', output)
        self.assertIn('"status": "error"', output)
        self.assertIn('"error_type": "AIProviderRequestError"', output)

    def test_no_openai_key_raises_configuration_error_without_mock_client(self):
        provider = OpenAIProvider(api_key="", client=None)

        with self.assertRaises(AIProviderConfigurationError):
            provider.generate_structured(
                prompt="Return JSON.",
                input_data={},
                response_model=ExampleResponse,
            )
