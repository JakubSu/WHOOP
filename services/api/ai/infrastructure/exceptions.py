class AIInfrastructureError(Exception):
    """Base exception for AI infrastructure failures."""


class AIProviderConfigurationError(AIInfrastructureError):
    """Raised when provider configuration is missing or invalid."""


class AIProviderRequestError(AIInfrastructureError):
    """Raised when a provider request fails."""


class AIProviderTimeoutError(AIProviderRequestError):
    """Raised when a provider request times out."""


class AIProviderRateLimitError(AIProviderRequestError):
    """Raised when a provider rate limit is reached."""


class AIProviderResponseValidationError(AIInfrastructureError):
    """Raised when a provider response cannot be validated."""


class PromptNotFoundError(AIInfrastructureError):
    """Raised when a requested prompt file does not exist."""


class InvalidPromptReferenceError(AIInfrastructureError):
    """Raised when a prompt reference is unsafe or malformed."""
