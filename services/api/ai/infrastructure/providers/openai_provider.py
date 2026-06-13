import json
import logging
import time
from typing import Any

from django.conf import settings
from pydantic import BaseModel

from ai.infrastructure.exceptions import (
    AIProviderConfigurationError,
    AIProviderRateLimitError,
    AIProviderRequestError,
    AIProviderResponseValidationError,
    AIProviderTimeoutError,
)
from ai.infrastructure.models import LLMRequestMetadata, LLMUsage, LoadedPrompt
from ai.infrastructure.prompt_loader import FileSystemPromptLoader, PromptLoader
from ai.infrastructure.structured_response_parser import (
    PydanticStructuredResponseParser,
    StructuredResponseParser,
)

logger = logging.getLogger(__name__)
MAX_LOG_TEXT_LENGTH = 8000


class OpenAIProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        client: Any | None = None,
        parser: StructuredResponseParser | None = None,
        prompt_loader: PromptLoader | None = None,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout if timeout is not None else settings.OPENAI_TIMEOUT
        self.client = client
        self.parser = parser or PydanticStructuredResponseParser()
        self.prompt_loader = prompt_loader or FileSystemPromptLoader()
        self.max_retries = max_retries

    def generate_structured(
        self,
        *,
        prompt: str,
        input_data: dict[str, Any],
        response_model: type[BaseModel],
        metadata: LLMRequestMetadata | None = None,
    ) -> BaseModel:
        call_metadata = metadata or LLMRequestMetadata()
        started_at = time.perf_counter()
        status = "error"
        error_type: str | None = None
        usage = LLMUsage()

        try:
            client = self._client()
            response = self._call_with_retries(
                client=client,
                prompt=prompt,
                input_data=input_data,
                response_model=response_model,
            )
            parsed = self._extract_parsed_response(response, response_model)
            usage = self._extract_usage(response)
            status = "success"
            return parsed
        except Exception as exc:
            mapped = self._map_exception(exc)
            error_type = type(mapped).__name__
            raise mapped from exc
        finally:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            self._log_request(
                metadata=call_metadata,
                prompt=prompt,
                response=parsed if status == "success" else None,
                usage=usage,
                latency_ms=latency_ms,
                status=status,
                error_type=error_type,
            )

    def generate_structured_from_prompt(
        self,
        *,
        namespace: str,
        name: str,
        version: str,
        input_data: dict[str, Any],
        response_model: type[BaseModel],
    ) -> BaseModel:
        loaded_prompt = self.prompt_loader.load(
            namespace=namespace,
            name=name,
            version=version,
        )
        prompt = self._render_prompt(loaded_prompt, input_data)
        metadata = LLMRequestMetadata(
            prompt_namespace=namespace,
            prompt_name=name,
            prompt_version=version,
        )
        return self.generate_structured(
            prompt=prompt,
            input_data=input_data,
            response_model=response_model,
            metadata=metadata,
        )

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        if not self.api_key:
            raise AIProviderConfigurationError("OPENAI_API_KEY must be configured.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AIProviderConfigurationError(
                "The OpenAI SDK is not installed. Install the 'openai' package."
            ) from exc
        self.client = OpenAI(api_key=self.api_key, timeout=self.timeout)
        return self.client

    def _call_with_retries(
        self,
        *,
        client: Any,
        prompt: str,
        input_data: dict[str, Any],
        response_model: type[BaseModel],
    ) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return client.responses.parse(
                    model=self.model,
                    input=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": json.dumps(input_data)},
                    ],
                    text_format=response_model,
                    timeout=self.timeout,
                )
            except Exception as exc:
                mapped = self._map_exception(exc)
                if not self._is_retryable(mapped) or attempt >= self.max_retries:
                    raise mapped from exc
                last_error = mapped
                time.sleep(0.1 * (attempt + 1))
        raise AIProviderRequestError("OpenAI request failed.") from last_error

    def _extract_parsed_response(
        self,
        response: Any,
        response_model: type[BaseModel],
    ) -> BaseModel:
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            if isinstance(parsed, response_model):
                return parsed
            return self.parser.parse(raw_response=parsed, response_model=response_model)

        output_text = getattr(response, "output_text", None)
        if output_text is not None:
            return self.parser.parse(
                raw_response=output_text,
                response_model=response_model,
            )

        if isinstance(response, dict):
            if "output_parsed" in response:
                return self.parser.parse(
                    raw_response=response["output_parsed"],
                    response_model=response_model,
                )
            if "output_text" in response:
                return self.parser.parse(
                    raw_response=response["output_text"],
                    response_model=response_model,
                )

        raise AIProviderResponseValidationError(
            "OpenAI response did not include a structured output."
        )

    def _extract_usage(self, response: Any) -> LLMUsage:
        usage = getattr(response, "usage", None)
        if usage is None and isinstance(response, dict):
            usage = response.get("usage")
        if usage is None:
            return LLMUsage()

        def read(name: str) -> int | None:
            if isinstance(usage, dict):
                return usage.get(name)
            return getattr(usage, name, None)

        input_tokens = read("input_tokens")
        output_tokens = read("output_tokens")
        total_tokens = read("total_tokens")
        return LLMUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    def _map_exception(self, exc: Exception) -> Exception:
        if isinstance(
            exc,
            (
                AIProviderConfigurationError,
                AIProviderRateLimitError,
                AIProviderRequestError,
                AIProviderResponseValidationError,
                AIProviderTimeoutError,
            ),
        ):
            return exc

        name = type(exc).__name__.lower()
        message = str(exc)
        if "timeout" in name or "timeout" in message.lower():
            return AIProviderTimeoutError("OpenAI request timed out.")
        if "ratelimit" in name or "rate limit" in message.lower():
            return AIProviderRateLimitError("OpenAI rate limit reached.")
        return AIProviderRequestError("OpenAI request failed.")

    def _is_retryable(self, exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                AIProviderRateLimitError,
                AIProviderRequestError,
                AIProviderTimeoutError,
            ),
        )

    def _render_prompt(self, prompt: LoadedPrompt, input_data: dict[str, Any]) -> str:
        render = getattr(self.prompt_loader, "render", None)
        if callable(render):
            return render(prompt, input_data)
        return prompt.template

    def _log_request(
        self,
        *,
        metadata: LLMRequestMetadata,
        prompt: str,
        response: BaseModel | dict[str, Any] | list[Any] | str | int | float | bool | None,
        usage: LLMUsage,
        latency_ms: int,
        status: str,
        error_type: str | None,
    ) -> None:
        log_payload = {
            "provider": self.provider_name,
            "model": self.model,
            "prompt_namespace": metadata.prompt_namespace,
            "prompt_name": metadata.prompt_name,
            "prompt_version": metadata.prompt_version,
            "prompt": self._stringify_log_value(prompt),
            "response": self._stringify_log_value(response),
            "latency_ms": latency_ms,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "status": status,
            "error_type": error_type,
        }
        logger.info(
            "llm_request %s",
            json.dumps(log_payload, sort_keys=True),
        )

    def _stringify_log_value(
        self,
        value: BaseModel | dict[str, Any] | list[Any] | str | int | float | bool | None,
    ) -> str | int | float | bool | None:
        if value is None or isinstance(value, (str, int, float, bool)):
            return self._truncate_text(value)
        if isinstance(value, BaseModel):
            value = value.model_dump(mode="json")
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return self._truncate_text(text)

    def _truncate_text(self, value: str | int | float | bool | None) -> str | int | float | bool | None:
        if not isinstance(value, str):
            return value
        if len(value) <= MAX_LOG_TEXT_LENGTH:
            return value
        return f"{value[:MAX_LOG_TEXT_LENGTH]}…<truncated>"
