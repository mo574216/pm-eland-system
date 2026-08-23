"""Canonical generic entity schema contract tests."""

from typing import cast

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.entity import EntityObject


def test_entity_object_is_generic_jsonb_canonical_model() -> None:
    table = cast(Table, EntityObject.__table__)
    assert isinstance(table.c.attributes.type, JSONB)
    assert "entity_attribute_values" not in table.metadata.tables
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.entity_type_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(table.c.parent_id.foreign_keys)).ondelete == "RESTRICT"
    assert any(constraint.name == "ck_entity_objects_status" for constraint in table.constraints)


def test_entity_object_has_required_scope_and_json_indexes() -> None:
    table = cast(Table, EntityObject.__table__)
    assert {index.name for index in table.indexes} == {
        "idx_entity_objects_workspace",
        "idx_entity_objects_type",
        "idx_entity_objects_parent",
        "idx_entity_objects_name",
        "idx_entity_objects_attributes_gin",
    }
    gin_index = next(
        index for index in table.indexes if index.name == "idx_entity_objects_attributes_gin"
    )
    assert gin_index.dialect_options["postgresql"]["using"] == "gin"
