import json
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from ai.infrastructure.exceptions import AIProviderResponseValidationError

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class StructuredResponseParser(Protocol):
    def parse(
        self,
        *,
        raw_response: str | dict[str, Any],
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        ...


class PydanticStructuredResponseParser:
    def parse(
        self,
        *,
        raw_response: str | dict[str, Any],
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        try:
            if isinstance(raw_response, str):
                return response_model.model_validate_json(raw_response)
            return response_model.model_validate(raw_response)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            raise AIProviderResponseValidationError(
                "LLM response did not match the expected structured schema."
            ) from exc
