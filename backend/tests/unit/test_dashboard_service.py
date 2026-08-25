"""Dashboard authorization and deterministic KPI projection tests."""

from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.core.permissions import PermissionCode
from app.models.identity import User
from app.models.workspace import Workspace
from app.repositories.dashboard import DashboardRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.dashboard import DashboardService


class Repo:
    async def summary_counts(self, _: object) -> tuple[int, int, int, int, int, int]:
        return (12, 4, 3, 2, 5, 7)


class WorkspaceRepo:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def accessible_workspace(self, *_: object) -> Workspace:
        return self.workspace

    async def workspace_permission_codes(self, *_: object) -> tuple[str, ...]:
        return ()


def actor(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="viewer",
        email="viewer@example.test",
        password_hash="unused",  # noqa: S106
        display_name="Viewer",
    )
    return AuthenticatedIdentity(
        user=user, roles=("VIEWER",), permissions=tuple(value.value for value in permissions)
    )


def service(identity: AuthenticatedIdentity, workspace: Workspace) -> DashboardService:
    result = DashboardService(cast(AsyncSession, object()), identity)
    result.repository = cast(DashboardRepository, Repo())
    result.workspace_repository = cast(WorkspaceRepository, WorkspaceRepo(workspace))
    return result


@pytest.mark.asyncio
async def test_summary_requires_dashboard_read() -> None:
    identity = actor()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=identity.user.id)
    with pytest.raises(PermissionDeniedError):
        await service(identity, workspace).summary(workspace.id)


@pytest.mark.asyncio
async def test_summary_returns_server_defined_counts_and_phase_percent() -> None:
    identity = actor(PermissionCode.DASHBOARD_READ)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=identity.user.id)
    result = await service(identity, workspace).summary(workspace.id)
    assert result.entity_count == 12
    assert result.document_count == 4
    assert result.phases.percent == 67
    assert result.deliverables.pending == 5
