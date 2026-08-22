"""Centralized effective-permission policy."""

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, Role
from app.repositories.auth import AuthRepository
from app.services.auth import AuthenticatedIdentity


class AuthorizationService:
    """Evaluate a server-resolved identity for protected operations."""

    def __init__(self, identity: AuthenticatedIdentity) -> None:
        self.identity = identity
        self._permissions = frozenset(identity.permissions)

    @property
    def role_codes(self) -> tuple[str, ...]:
        return self.identity.roles

    @property
    def permission_codes(self) -> frozenset[str]:
        return self._permissions

    def has_permission(self, permission: PermissionCode) -> bool:
        return permission.value in self._permissions

    def require_permission(self, permission: PermissionCode) -> None:
        if not self.has_permission(permission):
            raise PermissionDeniedError

    def require_all(self, permissions: Iterable[PermissionCode]) -> None:
        for permission in permissions:
            self.require_permission(permission)


@dataclass(frozen=True)
class AuditContext:
    request_id: UUID
    client_ip: str | None
    user_agent: str | None


class RoleAssignmentService:
    """Mutate global roles with privilege-escalation and audit enforcement."""

    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = AuthRepository(session)

    async def assign_role(
        self, target_user_id: UUID, role_code: str, audit: AuditContext
    ) -> tuple[Role, bool]:
        self.authorization.require_permission(PermissionCode.IDENTITY_MANAGE)
        async with self.session.begin():
            target = await self.repository.user_by_id(target_user_id)
            role = await self.repository.role_by_code(role_code)
            if target is None or role is None:
                raise ResourceNotFoundError
            granted_permissions = set(await self.repository.role_permission_codes(role.id))
            if not granted_permissions.issubset(self.authorization.permission_codes):
                raise PermissionDeniedError
            changed = await self.repository.assign_role(target.id, role.id)
            if changed:
                self.repository.add_audit_log(
                    AuditLog(
                        id=uuid4(),
                        request_id=audit.request_id,
                        user_id=self.actor.user.id,
                        action="ROLE_ASSIGNED",
                        resource_type="user_role",
                        resource_id=target.id,
                        before_state={"role_code": None},
                        after_state={"role_code": role.code},
                        client_ip=audit.client_ip,
                        user_agent=audit.user_agent,
                    )
                )
        return role, changed

    async def remove_role(
        self, target_user_id: UUID, role_code: str, audit: AuditContext
    ) -> tuple[Role, bool]:
        self.authorization.require_permission(PermissionCode.IDENTITY_MANAGE)
        async with self.session.begin():
            target = await self.repository.user_by_id(target_user_id)
            role = await self.repository.role_by_code(role_code)
            if target is None or role is None:
                raise ResourceNotFoundError
            changed = await self.repository.remove_role(target.id, role.id)
            if changed:
                self.repository.add_audit_log(
                    AuditLog(
                        id=uuid4(),
                        request_id=audit.request_id,
                        user_id=self.actor.user.id,
                        action="ROLE_REMOVED",
                        resource_type="user_role",
                        resource_id=target.id,
                        before_state={"role_code": role.code},
                        after_state={"role_code": None},
                        client_ip=audit.client_ip,
                        user_agent=audit.user_agent,
                    )
                )
        return role, changed
