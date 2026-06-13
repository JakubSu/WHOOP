from django.conf import settings

from ai.infrastructure.exceptions import AIProviderConfigurationError
from ai.infrastructure.llm_provider import LLMProvider
from ai.infrastructure.providers.openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    provider = getattr(settings, "AI_LLM_PROVIDER", "openai").lower()
    if provider == "openai":
        return OpenAIProvider()
    raise AIProviderConfigurationError(f"Unsupported AI_LLM_PROVIDER '{provider}'.")
