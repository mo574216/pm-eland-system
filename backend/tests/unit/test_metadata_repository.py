"""Metadata repository workspace-isolation query tests."""

from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable

from app.repositories.metadata import MetadataRepository


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
async def test_entity_type_lookup_requires_active_membership() -> None:
    session = CapturingSession()
    repository = MetadataRepository(cast(AsyncSession, session))

    await repository.accessible_entity_type(uuid4(), uuid4())

    sql = str(session.statements[0])
    assert "JOIN workspace_memberships" in sql
    assert "workspace_memberships.user_id" in sql
    assert "workspace_memberships.status" in sql
    assert "entity_types.deleted_at IS NULL" in sql


@pytest.mark.asyncio
async def test_entity_type_collection_scopes_items_and_count_to_membership() -> None:
    session = CapturingSession()
    repository = MetadataRepository(cast(AsyncSession, session))

    await repository.list_entity_types(
        uuid4(),
        uuid4(),
        page=1,
        page_size=50,
        active=True,
        search="process",
    )

    assert len(session.statements) == 2
    for statement in session.statements:
        sql = str(statement)
        assert "JOIN workspace_memberships" in sql
        assert "entity_types.workspace_id" in sql
        assert "workspace_memberships.user_id" in sql
        assert "workspace_memberships.status" in sql
