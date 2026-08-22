"""Generic entity repository workspace-scope tests."""

from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

from app.repositories.entity import EntityRepository


class CapturingSession:
    def __init__(self) -> None:
        self.statements: list[Executable] = []

    async def scalar(self, statement: Executable) -> None:
        self.statements.append(statement)

    async def scalars(self, statement: Executable) -> "EmptyScalars":
        self.statements.append(statement)
        return EmptyScalars()

    async def execute(self, statement: Executable) -> "EmptyRows":
        self.statements.append(statement)
        return EmptyRows()


class EmptyScalars:
    def all(self) -> list[object]:
        return []


class EmptyRows:
    def all(self) -> list[object]:
        return []

    def one_or_none(self) -> None:
        return None

    def mappings(self) -> "EmptyRows":
        return self


@pytest.mark.asyncio
async def test_entity_lookup_always_includes_workspace_and_deleted_scope() -> None:
    session = CapturingSession()
    repository = EntityRepository(cast(AsyncSession, session))

    await repository.entity_in_workspace(uuid4(), uuid4())

    sql = str(session.statements[0])
    assert "entity_objects.id" in sql
    assert "entity_objects.workspace_id" in sql
    assert "entity_objects.deleted_at IS NULL" in sql


@pytest.mark.asyncio
async def test_user_reference_requires_active_workspace_membership() -> None:
    session = CapturingSession()
    repository = EntityRepository(cast(AsyncSession, session))

    await repository.user_reference_exists(uuid4(), uuid4())

    sql = str(session.statements[0])
    assert "JOIN workspace_memberships" in sql
    assert "users.is_active" in sql
    assert "workspace_memberships.workspace_id" in sql
    assert "workspace_memberships.status" in sql


@pytest.mark.asyncio
async def test_entity_collection_items_and_count_are_membership_scoped() -> None:
    session = CapturingSession()
    repository = EntityRepository(cast(AsyncSession, session))

    await repository.list_entities(
        uuid4(),
        uuid4(),
        page=1,
        page_size=50,
        status="ACTIVE",
        entity_type_id=None,
        parent_id=None,
        search="فرایند",
    )

    assert len(session.statements) == 2
    for statement in session.statements:
        sql = str(statement)
        assert "JOIN workspace_memberships" in sql
        assert "entity_objects.workspace_id" in sql
        assert "workspace_memberships.user_id" in sql
        assert "workspace_memberships.status" in sql
        assert "regexp_replace" in sql


@pytest.mark.asyncio
async def test_hierarchy_uses_one_workspace_scoped_recursive_cte() -> None:
    session = CapturingSession()
    repository = EntityRepository(cast(AsyncSession, session))

    await repository.entity_tree(
        uuid4(),
        uuid4(),
        root_id=uuid4(),
        max_depth=3,
        include_type=True,
    )

    assert len(session.statements) == 1
    sql = str(session.statements[0])
    assert "WITH RECURSIVE entity_tree" in sql
    assert "UNION ALL" in sql
    assert "JOIN workspace_memberships" in sql
    assert "entity_objects.workspace_id" in sql
    assert "child.workspace_id" in sql
    assert "entity_objects.deleted_at IS NULL" in sql
    assert "child.deleted_at IS NULL" in sql
    assert "possible_child" in sql
    assert "ORDER BY entity_tree.path" in sql
