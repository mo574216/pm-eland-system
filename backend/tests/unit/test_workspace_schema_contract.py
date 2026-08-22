"""Workspace model and migration contract tests."""

from typing import cast

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.workspace import Workspace, WorkspaceMembership


def test_workspace_model_matches_database_contract() -> None:
    table = cast(Table, Workspace.__table__)

    assert set(table.columns.keys()) == {
        "id",
        "name",
        "slug",
        "description",
        "owner_id",
        "status",
        "configuration",
        "created_at",
        "updated_at",
        "archived_at",
        "deleted_at",
        "version",
    }
    assert isinstance(table.c.configuration.type, JSONB)
    assert table.c.configuration.nullable is False
    assert table.c.version.nullable is False
    assert {index.name for index in table.indexes} == {
        "idx_workspaces_owner",
        "idx_workspaces_status",
    }
    owner_foreign_key = next(iter(table.c.owner_id.foreign_keys))
    assert owner_foreign_key.target_fullname == "users.id"
    assert owner_foreign_key.ondelete == "SET NULL"
    assert any(constraint.name == "ck_workspaces_status" for constraint in table.constraints)


def test_workspace_membership_enforces_one_scoped_role_per_user() -> None:
    table = cast(Table, WorkspaceMembership.__table__)

    assert set(table.columns.keys()) == {
        "id",
        "workspace_id",
        "user_id",
        "role_id",
        "status",
        "created_at",
    }
    assert table.c.workspace_id.nullable is False
    assert table.c.user_id.nullable is False
    assert table.c.role_id.nullable is True
    assert {index.name for index in table.indexes} == {
        "idx_workspace_memberships_user",
        "idx_workspace_memberships_workspace",
    }
    assert any(
        constraint.name == "uq_workspace_memberships_workspace_user"
        for constraint in table.constraints
    )
    assert any(
        constraint.name == "ck_workspace_memberships_status" for constraint in table.constraints
    )

    foreign_keys = {
        column.name: next(iter(column.foreign_keys))
        for column in (table.c.workspace_id, table.c.user_id, table.c.role_id)
    }
    assert foreign_keys["workspace_id"].target_fullname == "workspaces.id"
    assert foreign_keys["workspace_id"].ondelete == "CASCADE"
    assert foreign_keys["user_id"].target_fullname == "users.id"
    assert foreign_keys["user_id"].ondelete == "CASCADE"
    assert foreign_keys["role_id"].target_fullname == "roles.id"
    assert foreign_keys["role_id"].ondelete == "SET NULL"
