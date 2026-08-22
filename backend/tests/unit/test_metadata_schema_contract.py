"""Generic metadata model contract tests."""

from typing import cast

from sqlalchemy import CheckConstraint, Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.metadata import SUPPORTED_ATTRIBUTE_TYPES, AttributeDefinition, EntityType


def test_entity_types_are_workspace_scoped_and_generic() -> None:
    table = cast(Table, EntityType.__table__)
    assert set(table.columns) == {
        table.c.id,
        table.c.workspace_id,
        table.c.key,
        table.c.name,
        table.c.plural_name,
        table.c.description,
        table.c.icon_key,
        table.c.is_active,
        table.c.configuration,
        table.c.created_by,
        table.c.created_at,
        table.c.updated_at,
        table.c.deleted_at,
        table.c.version,
    }
    assert isinstance(table.c.configuration.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert {index.name for index in table.indexes} == {
        "idx_entity_types_workspace",
        "idx_entity_types_active",
    }
    assert any(
        constraint.name == "uq_entity_types_workspace_key" for constraint in table.constraints
    )


def test_attribute_definitions_enforce_canonical_types_and_keys() -> None:
    table = cast(Table, AttributeDefinition.__table__)
    assert isinstance(table.c.default_value.type, JSONB)
    assert isinstance(table.c.validation_config.type, JSONB)
    assert isinstance(table.c.display_config.type, JSONB)
    assert isinstance(table.c.inheritance_config.type, JSONB)
    assert next(iter(table.c.entity_type_id.foreign_keys)).ondelete == "CASCADE"
    assert {index.name for index in table.indexes} == {
        "idx_attribute_definitions_type",
        "idx_attribute_definitions_active",
    }
    assert any(
        constraint.name == "uq_attribute_definitions_type_key" for constraint in table.constraints
    )
    data_type_check = cast(
        CheckConstraint,
        next(
            constraint
            for constraint in table.constraints
            if constraint.name == "ck_attribute_definitions_data_type"
        ),
    )
    check_sql = str(data_type_check.sqltext)
    assert all(f"'{value}'" in check_sql for value in SUPPORTED_ATTRIBUTE_TYPES)
