"""Safe domain errors for AI tools."""


class ToolNotFoundError(ValueError):
    """Raised when a requested record is missing or outside the caller's scope."""


class ToolValidationError(ValueError):
    """Raised when a tool input cannot be safely applied."""
