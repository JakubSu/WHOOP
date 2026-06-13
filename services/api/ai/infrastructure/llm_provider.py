from typing import Any, Protocol

from pydantic import BaseModel

from ai.infrastructure.models import LLMRequestMetadata


class LLMProvider(Protocol):
    def generate_structured(
        self,
        *,
        prompt: str,
        input_data: dict[str, Any],
        response_model: type[BaseModel],
        metadata: LLMRequestMetadata | None = None,
    ) -> BaseModel:
        ...
