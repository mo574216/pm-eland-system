"""Dashboard persistence contract tests."""

from typing import cast

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.dashboard import Dashboard


def test_dashboard_is_workspace_scoped_and_metadata_defined() -> None:
    table = cast(Table, Dashboard.__table__)
    assert set(table.columns.keys()) == {
        "id",
        "workspace_id",
        "name",
        "description",
        "configuration",
        "created_by",
        "created_at",
        "updated_at",
        "version",
    }
    assert isinstance(table.c.configuration.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
