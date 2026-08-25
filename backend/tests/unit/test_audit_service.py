"""Audit query authorization and workspace projection tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, User
from app.models.workspace import Workspace
from app.repositories.audit import AuditEntryRecord, AuditRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.audit import AuditService
from app.services.auth import AuthenticatedIdentity


class Repo:
    async def list_workspace_history(
        self, *_: object, **__: object
    ) -> tuple[tuple[AuditEntryRecord, ...], int]:
        log = AuditLog(
            id=uuid4(),
            workspace_id=uuid4(),
            action="ENTITY_UPDATED",
            resource_type="entity",
            source="API",
            created_at=datetime(2026, 8, 25, tzinfo=UTC),
        )
        return ((AuditEntryRecord(log, "akbar", "Akbar"),), 1)


class WorkspaceRepo:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def accessible_workspace(self, *_: object) -> Workspace:
        return self.workspace

    async def workspace_permission_codes(self, *_: object) -> tuple[str, ...]:
        return ()


def build_service(*permissions: PermissionCode) -> tuple[AuditService, Workspace]:
    user = User(id=uuid4(), username="viewer", email="viewer@example.test", password_hash="unused")  # noqa: S106
    actor = AuthenticatedIdentity(
        user=user,
        roles=("VIEWER",),
        permissions=tuple(p.value for p in permissions),
    )
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=user.id)
    result = AuditService(cast(AsyncSession, object()), actor)
    result.repository = cast(AuditRepository, Repo())
    result.workspace_repository = cast(WorkspaceRepository, WorkspaceRepo(workspace))
    return result, workspace


@pytest.mark.asyncio
async def test_history_requires_audit_read() -> None:
    service, workspace = build_service()
    with pytest.raises(PermissionDeniedError):
        await service.history(
            workspace.id,
            page=1,
            page_size=25,
            resource_type=None,
            resource_id=None,
            user_id=None,
            action=None,
            from_at=None,
            to_at=None,
        )


@pytest.mark.asyncio
async def test_history_returns_actor_and_read_only_state() -> None:
    service, workspace = build_service(PermissionCode.AUDIT_READ)
    result = await service.history(
        workspace.id,
        page=1,
        page_size=25,
        resource_type=None,
        resource_id=None,
        user_id=None,
        action=None,
        from_at=None,
        to_at=None,
    )
    assert result.total == 1
    assert result.items[0].actor_name == "Akbar"
    assert result.items[0].action == "ENTITY_UPDATED"
