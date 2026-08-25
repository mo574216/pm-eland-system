"""Workspace isolation, authorization, concurrency, and audit tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, StaleVersionError, WorkspaceAccessDeniedError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, Role, User
from app.models.workspace import Workspace, WorkspaceMembership
from app.repositories.workspace import WorkspaceMemberRecord, WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.workspace import WorkspaceService


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="manager",
        email="manager@example.test",
        password_hash="unused-in-workspace-test",  # noqa: S106
        display_name="Manager",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("PROJECT_MANAGER",),
        permissions=tuple(permission.value for permission in permissions),
    )


def workspace(owner_id: UUID) -> Workspace:
    return Workspace(
        id=uuid4(),
        name="Workspace A",
        slug="workspace-a",
        owner_id=owner_id,
        status="ACTIVE",
        configuration={},
        version=1,
    )


class FakeWorkspaceRepository:
    def __init__(self, scoped_workspace: Workspace | None) -> None:
        self.scoped_workspace = scoped_workspace
        self.workspace_permissions: tuple[str, ...] = ()
        self.role_permissions: tuple[str, ...] = ()
        self.updated_workspace: Workspace | None = scoped_workspace
        self.target_user: User | None = None
        self.target_role: Role | None = None
        self.existing_membership: WorkspaceMembership | None = None
        self.workspaces: list[Workspace] = []
        self.memberships: list[WorkspaceMembership] = []
        self.audit_logs: list[AuditLog] = []
        self.candidates: tuple[User, ...] = ()
        self.roles: tuple[Role, ...] = ()
        self.permissions_by_role: dict[UUID, tuple[str, ...]] = {}

    def add_workspace(self, value: Workspace) -> None:
        self.workspaces.append(value)

    def add_membership(self, value: WorkspaceMembership) -> None:
        self.memberships.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for workspace_value in self.workspaces:
            workspace_value.created_at = now
            workspace_value.updated_at = now
        for membership_value in self.memberships:
            membership_value.created_at = now

    async def workspace_by_slug(self, _: str) -> Workspace | None:
        return None

    async def accessible_workspace(self, _: UUID, __: UUID) -> Workspace | None:
        return self.scoped_workspace

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return self.workspace_permissions

    async def list_accessible_workspaces(
        self, *_: object, **__: object
    ) -> tuple[tuple[Workspace, ...], int]:
        items = tuple(self.workspaces)
        return items, len(items)

    async def update_workspace(
        self, _: UUID, __: int, values: dict[str, object]
    ) -> Workspace | None:
        if self.updated_workspace is not None:
            for key, value in values.items():
                setattr(self.updated_workspace, key, value)
            self.updated_workspace.version += 1
        return self.updated_workspace

    async def user_by_id(self, _: UUID) -> User | None:
        return self.target_user

    async def role_by_id(self, _: UUID) -> Role | None:
        return self.target_role

    async def role_permission_codes(self, _: UUID) -> tuple[str, ...]:
        return self.permissions_by_role.get(_, self.role_permissions)

    async def search_member_candidates(
        self, _: UUID, __: str, ___: int
    ) -> tuple[User, ...]:
        return self.candidates

    async def list_roles(self) -> tuple[Role, ...]:
        return self.roles

    async def membership(self, _: UUID, __: UUID) -> WorkspaceMembership | None:
        return self.existing_membership

    async def list_members(self, _: UUID) -> tuple[WorkspaceMemberRecord, ...]:
        return ()

    async def remove_membership(self, _: UUID) -> bool:
        return True


def service(actor: AuthenticatedIdentity, repository: FakeWorkspaceRepository) -> WorkspaceService:
    result = WorkspaceService(cast(AsyncSession, FakeSession()), actor)
    result.repository = cast(WorkspaceRepository, repository)
    return result


def audit_context() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_workspace_creation_adds_owner_membership_and_audit_atomically() -> None:
    actor = identity(PermissionCode.WORKSPACE_CREATE)
    repository = FakeWorkspaceRepository(None)

    created = await service(actor, repository).create_workspace(
        name="Workspace A",
        slug="workspace-a",
        description=None,
        audit=audit_context(),
    )

    assert created.owner_id == actor.user.id
    assert repository.memberships[0].workspace_id == created.id
    assert repository.memberships[0].user_id == actor.user.id
    assert repository.memberships[0].status == "ACTIVE"
    assert repository.audit_logs[0].action == "WORKSPACE_CREATED"
    assert repository.audit_logs[0].workspace_id == created.id


@pytest.mark.asyncio
async def test_inaccessible_workspace_is_rejected_before_permission_evaluation() -> None:
    actor = identity(PermissionCode.WORKSPACE_MANAGE)

    with pytest.raises(WorkspaceAccessDeniedError):
        await service(actor, FakeWorkspaceRepository(None)).update_workspace(
            uuid4(),
            expected_version=1,
            values={"name": "Changed"},
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_stale_workspace_update_does_not_write_audit() -> None:
    actor = identity(PermissionCode.WORKSPACE_MANAGE)
    repository = FakeWorkspaceRepository(workspace(actor.user.id))
    repository.updated_workspace = None
    assert repository.scoped_workspace is not None

    with pytest.raises(StaleVersionError):
        await service(actor, repository).update_workspace(
            repository.scoped_workspace.id,
            expected_version=99,
            values={"name": "Changed"},
            audit=audit_context(),
        )

    assert repository.audit_logs == []


@pytest.mark.asyncio
async def test_actor_cannot_grant_workspace_role_permissions_they_do_not_possess() -> None:
    actor = identity(PermissionCode.WORKSPACE_MANAGE)
    scoped_workspace = workspace(actor.user.id)
    repository = FakeWorkspaceRepository(scoped_workspace)
    repository.target_user = identity().user
    repository.target_role = Role(id=uuid4(), code="PROJECT_MANAGER", name="Manager")
    repository.role_permissions = (PermissionCode.PHASE_UNLOCK.value,)

    with pytest.raises(PermissionDeniedError):
        await service(actor, repository).add_member(
            scoped_workspace.id,
            user_id=repository.target_user.id,
            role_id=repository.target_role.id,
            audit=audit_context(),
        )

    assert repository.memberships == []
    assert repository.audit_logs == []


@pytest.mark.asyncio
async def test_workspace_role_can_supply_manage_permission_within_membership() -> None:
    actor = identity()
    scoped_workspace = workspace(actor.user.id)
    repository = FakeWorkspaceRepository(scoped_workspace)
    repository.workspace_permissions = (PermissionCode.WORKSPACE_MANAGE.value,)

    assert await service(actor, repository).list_members(scoped_workspace.id) == ()


@pytest.mark.asyncio
async def test_member_candidate_search_requires_workspace_manage() -> None:
    actor = identity()
    scoped_workspace = workspace(actor.user.id)

    with pytest.raises(PermissionDeniedError):
        await service(actor, FakeWorkspaceRepository(scoped_workspace)).search_member_candidates(
            scoped_workspace.id, search="ali", limit=10
        )


@pytest.mark.asyncio
async def test_role_options_only_include_roles_actor_may_assign() -> None:
    actor = identity(PermissionCode.WORKSPACE_MANAGE, PermissionCode.ENTITY_READ)
    scoped_workspace = workspace(actor.user.id)
    repository = FakeWorkspaceRepository(scoped_workspace)
    reader = Role(id=uuid4(), code="READER", name="Reader")
    manager = Role(id=uuid4(), code="MANAGER", name="Manager")
    repository.roles = (reader, manager)
    repository.permissions_by_role = {
        reader.id: (PermissionCode.ENTITY_READ.value,),
        manager.id: (PermissionCode.WORKSPACE_MANAGE.value, PermissionCode.PHASE_UNLOCK.value),
    }

    options = await service(actor, repository).list_assignable_roles(scoped_workspace.id)

    assert options == (reader,)
