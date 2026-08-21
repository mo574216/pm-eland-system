"""Request-local correlation context."""

from contextvars import ContextVar, Token

_request_id: ContextVar[str] = ContextVar("request_id", default="unknown")


def get_request_id() -> str:
    """Return the active request ID."""
    return _request_id.get()


def set_request_id(value: str) -> Token[str]:
    """Set the active request ID and return its reset token."""
    return _request_id.set(value)


def reset_request_id(token: Token[str]) -> None:
    """Restore the previous request ID context."""
    _request_id.reset(token)
