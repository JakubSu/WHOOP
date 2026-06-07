class WhoopError(Exception):
    pass


class WhoopAuthError(WhoopError):
    pass


class WhoopRateLimitError(WhoopError):
    pass


class WhoopNotFoundError(WhoopError):
    pass


class WhoopValidationError(WhoopError):
    pass


class WhoopServerError(WhoopError):
    pass


class WhoopParseError(WhoopError):
    pass


class WhoopConnectionNotFound(WhoopError):
    pass
