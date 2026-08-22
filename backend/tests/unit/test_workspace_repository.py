"""Workspace repository query-scope tests."""

from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

from app.repositories.workspace import WorkspaceRepository


class EmptyScalars:
    def all(self) -> list[object]:
        return []


class CapturingSession:
    def __init__(self) -> None:
        self.statements: list[Executable] = []

    async def scalar(self, statement: Executable) -> None:
        self.statements.append(statement)

    async def scalars(self, statement: Executable) -> EmptyScalars:
        self.statements.append(statement)
        return EmptyScalars()


@pytest.mark.asyncio
async def test_single_workspace_query_requires_active_user_membership() -> None:
    session = CapturingSession()
    repository = WorkspaceRepository(cast(AsyncSession, session))

    await repository.accessible_workspace(uuid4(), uuid4())

    sql = str(session.statements[0])
    assert "JOIN workspace_memberships" in sql
    assert "workspace_memberships.user_id" in sql
    assert "workspace_memberships.status" in sql
    assert "workspaces.deleted_at IS NULL" in sql


@pytest.mark.asyncio
async def test_workspace_collection_query_scopes_items_and_count_to_membership() -> None:
    session = CapturingSession()
    repository = WorkspaceRepository(cast(AsyncSession, session))

    await repository.list_accessible_workspaces(
        uuid4(),
        can_read_globally=True,
        page=1,
        page_size=50,
        status=None,
        search=None,
    )

    assert len(session.statements) == 2
    for statement in session.statements:
        sql = str(statement)
        assert "JOIN workspace_memberships" in sql
        assert "workspace_memberships.user_id" in sql
        assert "workspace_memberships.status" in sql
        assert "workspaces.deleted_at IS NULL" in sql


@pytest.mark.asyncio
async def test_workspace_role_read_permission_is_required_without_global_read() -> None:
    session = CapturingSession()
    repository = WorkspaceRepository(cast(AsyncSession, session))

    await repository.list_accessible_workspaces(
        uuid4(),
        can_read_globally=False,
        page=1,
        page_size=50,
        status=None,
        search=None,
    )

    for statement in session.statements:
        sql = str(statement)
        assert "JOIN role_permissions" in sql
        assert "JOIN permissions" in sql
        assert "permissions.code" in sql
