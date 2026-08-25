"""Phase authorization, locking, audit, and shared policy tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceLockedError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, User
from app.models.phase import Phase
from app.models.workspace import Workspace
from app.repositories.phase import PhaseRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.phase import LockPolicyService, PhaseService


class Transaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class Session:
    def begin(self) -> Transaction:
        return Transaction()


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="manager",
        email="m@example.test",
        password_hash="unused",  # noqa: S106
        display_name="مدیر",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("PROJECT_MANAGER",),
        permissions=tuple(value.value for value in permissions),
    )


def phase(workspace_id: UUID, *, locked: bool = False) -> Phase:
    value = Phase(
        id=uuid4(),
        workspace_id=workspace_id,
        key="phase_demo",
        name="Demo",
        sequence_number=1,
        status="PLANNED",
        is_locked=locked,
        version=1,
    )
    value.created_at = datetime.now(UTC)
    value.updated_at = datetime.now(UTC)
    return value


class PhaseRepo:
    def __init__(self, value: Phase) -> None:
        self.value = value
        self.audits: list[AuditLog] = []

    async def accessible_phase(self, *_: object, **__: object) -> Phase:
        return self.value

    async def set_lock(self, _: UUID, *, locked: bool, actor_id: UUID) -> Phase:
        self.value.is_locked = locked
        self.value.locked_by = actor_id if locked else None
        self.value.version += 1
        return self.value

    def add_audit_log(self, value: AuditLog) -> None:
        self.audits.append(value)


class WorkspaceRepo:
    def __init__(self, value: Workspace) -> None:
        self.value = value

    async def accessible_workspace(self, *_: object) -> Workspace:
        return self.value

    async def workspace_permission_codes(self, *_: object) -> tuple[str, ...]:
        return ()


@pytest.mark.asyncio
async def test_lock_and_unlock_use_explicit_permissions_and_audit() -> None:
    actor = identity(PermissionCode.PHASE_LOCK, PermissionCode.PHASE_UNLOCK)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    repository = PhaseRepo(phase(workspace.id))
    service = PhaseService(cast(AsyncSession, Session()), actor)
    service.repository = cast(PhaseRepository, repository)
    service.workspace_repository = cast(WorkspaceRepository, WorkspaceRepo(workspace))
    context = AuditContext(uuid4(), "127.0.0.1", "test")

    locked = await service.set_locked(repository.value.id, locked=True, audit=context)
    unlocked = await service.set_locked(repository.value.id, locked=False, audit=context)

    assert locked.id == unlocked.id
    assert [item.action for item in repository.audits] == ["PHASE_LOCKED", "PHASE_UNLOCKED"]


@pytest.mark.asyncio
async def test_shared_lock_policy_rejects_locked_phase() -> None:
    actor = identity()
    value = phase(uuid4(), locked=True)
    policy = LockPolicyService(cast(AsyncSession, Session()), actor)
    policy.repository = cast(PhaseRepository, PhaseRepo(value))

    with pytest.raises(ResourceLockedError):
        await policy.assert_phase_mutable(value.id)
