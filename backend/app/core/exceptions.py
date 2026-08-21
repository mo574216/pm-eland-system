"""Typed application exception hierarchy."""

from typing import Any


class ApplicationError(Exception):
    """Base class for errors safe to map to a stable public response."""

    def __init__(
        self,
        *,
        code: str,
        public_message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.status_code = status_code
        self.details = details or {}


class DependencyUnavailableError(ApplicationError):
    """A critical runtime dependency cannot currently serve requests."""

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="DEPENDENCY_UNAVAILABLE",
            public_message="A required service is unavailable.",
            status_code=503,
            details=details,
        )
