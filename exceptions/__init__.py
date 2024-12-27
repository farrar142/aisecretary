class RequestLimitError(Exception): ...


class ExecutionLimitExceededError(Exception):
    """Raised when a function exceeds the allowed execution limit."""

    pass


class RateLimitExceededError(Exception):
    """Raised when a function exceeds the allowed rate limit."""

    pass
