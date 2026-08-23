"""Canonical logical-document and immutable-version schema contract tests."""

from typing import cast

from sqlalchemy import CheckConstraint, Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.document import Document, DocumentVersion


def test_document_is_workspace_scoped_and_points_to_a_current_version() -> None:
    table = cast(Table, Document.__table__)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.entity_id.foreign_keys)).ondelete == "CASCADE"
    current = next(iter(table.c.current_version_id.foreign_keys))
    assert current.target_fullname == "document_versions.id"
    assert current.ondelete == "SET NULL"
    assert {index.name for index in table.indexes} == {"idx_documents_workspace_entity"}
    assert any(
        constraint.name == "ck_documents_lifecycle_status"
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    )


def test_document_versions_are_append_only_identified_and_storage_safe() -> None:
    table = cast(Table, DocumentVersion.__table__)
    assert isinstance(table.c.metadata.type, JSONB)
    assert next(iter(table.c.document_id.foreign_keys)).ondelete == "CASCADE"
    assert any(constraint.name == "uq_document_versions_number" for constraint in table.constraints)
    assert {index.name for index in table.indexes} == {
        "idx_document_versions_document",
        "uq_document_object_key",
    }
    assert next(index for index in table.indexes if index.name == "uq_document_object_key").unique
    checks = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert checks == {
        "ck_document_versions_number_positive",
        "ck_document_versions_file_size",
        "ck_document_versions_scan_status",
        "ck_document_versions_preview_status",
    }
