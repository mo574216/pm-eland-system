"""Backend-authoritative permission dependencies."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends

from app.api.dependencies.authentication import get_current_identity
from app.core.permissions import PermissionCode
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuthorizationService

PermissionDependency = Callable[..., Coroutine[Any, Any, AuthenticatedIdentity]]


def require_permission(permission: PermissionCode) -> PermissionDependency:
    """Create a dependency that rejects identities without a canonical permission."""

    async def dependency(
        identity: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    ) -> AuthenticatedIdentity:
        AuthorizationService(identity).require_permission(permission)
        return identity

    return dependency
