"""Canonical metadata-driven form schema contract tests."""

from typing import cast

from sqlalchemy import CheckConstraint, Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.form import FormDefinition, FormField, FormInstance


def test_form_definition_preserves_workspace_key_versions() -> None:
    table = cast(Table, FormDefinition.__table__)
    assert isinstance(table.c.schema_json.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.entity_type_id.foreign_keys)).ondelete == "RESTRICT"
    assert any(
        constraint.name == "uq_form_definitions_workspace_key_version"
        for constraint in table.constraints
    )
    assert {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    } == {
        "ck_form_definitions_version_positive",
        "ck_form_definitions_lifecycle_status",
    }
    assert {index.name for index in table.indexes} == {
        "idx_form_definitions_workspace_status",
        "idx_form_definitions_entity_type",
    }


def test_form_fields_are_generic_metadata_and_definition_scoped() -> None:
    table = cast(Table, FormField.__table__)
    for column_name in (
        "configuration",
        "visibility_rule",
        "validation_rule",
        "inheritance_rule",
    ):
        assert isinstance(table.c[column_name].type, JSONB)
    assert next(iter(table.c.form_definition_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.attribute_definition_id.foreign_keys)).ondelete == "SET NULL"
    assert any(
        constraint.name == "uq_form_fields_definition_key" for constraint in table.constraints
    )
    assert {index.name for index in table.indexes} == {"idx_form_fields_definition_order"}


def test_form_instances_retain_exact_definition_and_structured_values() -> None:
    table = cast(Table, FormInstance.__table__)
    assert isinstance(table.c.values_json.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.form_definition_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(table.c.entity_id.foreign_keys)).ondelete == "CASCADE"
    assert {index.name for index in table.indexes} == {
        "idx_form_instances_workspace",
        "idx_form_instances_entity",
        "idx_form_instances_form",
        "idx_form_instances_values_gin",
    }
    gin = next(index for index in table.indexes if index.name == "idx_form_instances_values_gin")
    assert gin.dialect_options["postgresql"]["using"] == "gin"
    status = cast(
        CheckConstraint,
        next(
            constraint
            for constraint in table.constraints
            if constraint.name == "ck_form_instances_status"
        ),
    )
    assert all(
        expected in str(status.sqltext)
        for expected in ("DRAFT", "SUBMITTED", "APPROVED", "REVISION_REQUESTED")
    )
