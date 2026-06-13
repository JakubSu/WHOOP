from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class LLMRequestMetadata(BaseModel):
    prompt_namespace: str | None = None
    prompt_name: str | None = None
    prompt_version: str | None = None
    correlation_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class LLMUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class LLMCallResult(BaseModel):
    result: BaseModel
    usage: LLMUsage = Field(default_factory=LLMUsage)
    model: str
    provider: str
    latency_ms: int

    model_config = {"arbitrary_types_allowed": True}


class LoadedPrompt(BaseModel):
    namespace: str
    name: str
    version: str
    template: str
    path: Path

    model_config = {"arbitrary_types_allowed": True}
