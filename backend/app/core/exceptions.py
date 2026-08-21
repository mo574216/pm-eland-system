"""Typed application exception hierarchy."""

from typing import Any

from app.core.localization import public_error_message


class ApplicationError(Exception):
    """Base class for errors safe to map to a stable public response."""

    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        resolved_message = public_error_message(code)
        super().__init__(resolved_message)
        self.code = code
        self.public_message = resolved_message
        self.status_code = status_code
        self.details = details or {}


class DependencyUnavailableError(ApplicationError):
    """A critical runtime dependency cannot currently serve requests."""

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="DEPENDENCY_UNAVAILABLE",
            status_code=503,
            details=details,
        )
