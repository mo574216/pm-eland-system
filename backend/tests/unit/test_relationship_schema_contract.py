"""Generic relationship schema contract tests."""

from typing import cast

from sqlalchemy import CheckConstraint, Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.relationship import EntityRelationship, RelationshipType


def test_relationship_type_is_workspace_scoped_metadata() -> None:
    table = cast(Table, RelationshipType.__table__)
    assert isinstance(table.c.configuration.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.source_type_id.foreign_keys)).ondelete == "SET NULL"
    assert next(iter(table.c.target_type_id.foreign_keys)).ondelete == "SET NULL"
    assert {index.name for index in table.indexes} == {"idx_relationship_types_workspace_active"}
    assert any(
        constraint.name == "uq_relationship_types_workspace_key" for constraint in table.constraints
    )
    directionality = cast(
        CheckConstraint,
        next(
            constraint
            for constraint in table.constraints
            if constraint.name == "ck_relationship_types_directionality"
        ),
    )
    assert "'DIRECTED'" in str(directionality.sqltext)
    assert "'UNDIRECTED'" in str(directionality.sqltext)


def test_entity_relationship_supports_generic_many_to_many_links() -> None:
    table = cast(Table, EntityRelationship.__table__)
    assert isinstance(table.c.attributes.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.relationship_type_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(table.c.source_entity_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.target_entity_id.foreign_keys)).ondelete == "CASCADE"
    assert {index.name for index in table.indexes} == {
        "idx_relationships_workspace",
        "idx_relationships_source",
        "idx_relationships_target",
        "idx_relationships_type",
    }
    assert any(
        constraint.name == "ck_entity_relationships_distinct_entities"
        for constraint in table.constraints
    )
    assert not any(constraint.name == "uq_relationship_active" for constraint in table.constraints)
