from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from ai.infrastructure.models import LLMRequestMetadata

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LLMProvider(Protocol):
    def generate_structured(
        self,
        *,
        prompt: str,
        input_data: dict[str, Any],
        response_model: type[ResponseModelT],
        metadata: LLMRequestMetadata | None = None,
    ) -> ResponseModelT:
        ...
