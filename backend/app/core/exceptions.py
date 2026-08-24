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


class InvalidCredentialsError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="AUTH_INVALID_CREDENTIALS", status_code=401)


class AuthenticationRequiredError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="AUTH_REQUIRED", status_code=401)


class AuthenticationExpiredError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="AUTH_TOKEN_EXPIRED", status_code=401)


class PermissionDeniedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="PERMISSION_DENIED", status_code=403)


class WorkspaceAccessDeniedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="WORKSPACE_ACCESS_DENIED", status_code=403)


class ResourceNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="RESOURCE_NOT_FOUND", status_code=404)


class ResourceConflictError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="RESOURCE_CONFLICT", status_code=409)


class ImportValidationFailedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="IMPORT_VALIDATION_FAILED", status_code=422)


class ImportConflictsUnresolvedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="IMPORT_CONFLICTS_UNRESOLVED", status_code=409)


class ImportAlreadyCommittedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="IMPORT_ALREADY_COMMITTED", status_code=409)


class StaleVersionError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="STALE_VERSION", status_code=409)


class HierarchyCycleError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="HIERARCHY_CYCLE", status_code=409)


class InvalidMetadataError(ApplicationError):
    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="INVALID_METADATA", status_code=422, details=details)


class FormValidationError(ApplicationError):
    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="VALIDATION_ERROR", status_code=422, details=details)


class InvalidRelationshipError(ApplicationError):
    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="INVALID_RELATIONSHIP", status_code=422, details=details)


class FileTooLargeError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="FILE_TOO_LARGE", status_code=413)


class FileTypeNotAllowedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="FILE_TYPE_NOT_ALLOWED", status_code=415)


class FileScanFailedError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(code="FILE_SCAN_FAILED", status_code=422)
