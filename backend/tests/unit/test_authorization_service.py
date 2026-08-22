"""Central authorization policy tests."""

from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest
import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, Role, User
from app.repositories.auth import AuthRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService, RoleAssignmentService


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="analyst1",
        email="analyst@example.test",
        password_hash="unused-in-authorization-test",  # noqa: S106
        display_name="Analyst One",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("ANALYST",),
        permissions=tuple(permission.value for permission in permissions),
    )


def test_permission_registry_matches_canonical_contract() -> None:
    contract_path = Path(__file__).parents[3] / "contracts" / "permissions.yaml"
    contract = cast(dict[str, Any], yaml.safe_load(contract_path.read_text(encoding="utf-8")))

    assert {permission.value for permission in PermissionCode} == {
        definition["code"] for definition in contract["permissions"]
    }


def test_authorization_service_allows_effective_permission() -> None:
    service = AuthorizationService(identity(PermissionCode.ENTITY_READ))

    service.require_permission(PermissionCode.ENTITY_READ)

    assert service.has_permission(PermissionCode.ENTITY_READ) is True
    assert service.role_codes == ("ANALYST",)


def test_authorization_service_denies_missing_permission() -> None:
    service = AuthorizationService(identity(PermissionCode.ENTITY_READ))

    with pytest.raises(PermissionDeniedError):
        service.require_permission(PermissionCode.FORM_DESIGN)


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()


class FakeRoleRepository:
    def __init__(self, target: User, role: Role, permissions: tuple[str, ...]) -> None:
        self.target = target
        self.role = role
        self.permissions = permissions
        self.assigned = False
        self.audit_logs: list[AuditLog] = []

    async def user_by_id(self, _: object) -> User:
        return self.target

    async def role_by_code(self, _: str) -> Role:
        return self.role

    async def role_permission_codes(self, _: object) -> tuple[str, ...]:
        return self.permissions

    async def assign_role(self, _: object, __: object) -> bool:
        self.assigned = True
        return True

    async def remove_role(self, _: object, __: object) -> bool:
        self.assigned = False
        return True

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.audit_logs.append(audit_log)


def role_assignment_service(
    actor: AuthenticatedIdentity, repository: FakeRoleRepository
) -> RoleAssignmentService:
    service = RoleAssignmentService(cast(AsyncSession, FakeSession()), actor)
    service.repository = cast(AuthRepository, repository)
    return service


def audit_context() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_role_assignment_is_atomic_and_audited() -> None:
    target = identity().user
    role = Role(id=uuid4(), code="VIEWER", name="Viewer", is_system=True)
    repository = FakeRoleRepository(target, role, (PermissionCode.ENTITY_READ.value,))
    actor = identity(PermissionCode.IDENTITY_MANAGE, PermissionCode.ENTITY_READ)

    assigned_role, changed = await role_assignment_service(actor, repository).assign_role(
        target.id, role.code, audit_context()
    )

    assert assigned_role is role
    assert changed is True
    assert repository.assigned is True
    assert len(repository.audit_logs) == 1
    assert repository.audit_logs[0].action == "ROLE_ASSIGNED"
    assert repository.audit_logs[0].created_at is None


@pytest.mark.asyncio
async def test_actor_cannot_grant_permissions_they_do_not_possess() -> None:
    target = identity().user
    role = Role(id=uuid4(), code="PROJECT_MANAGER", name="Manager", is_system=True)
    repository = FakeRoleRepository(target, role, (PermissionCode.PHASE_UNLOCK.value,))
    actor = identity(PermissionCode.IDENTITY_MANAGE)

    with pytest.raises(PermissionDeniedError):
        await role_assignment_service(actor, repository).assign_role(
            target.id, role.code, audit_context()
        )

    assert repository.assigned is False
    assert repository.audit_logs == []
