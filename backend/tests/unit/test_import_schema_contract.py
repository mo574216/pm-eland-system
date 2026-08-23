"""Canonical staged-import persistence contract tests."""

from typing import cast

from sqlalchemy import CheckConstraint, Table
from sqlalchemy.dialects.postgresql import JSONB

from app.models.import_job import ImportConflict, ImportJob, ImportMapping, ImportProfile


def check_names(table: Table) -> set[str | None]:
    return {
        cast(str | None, constraint.name)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_profiles_and_mappings_are_generic_workspace_metadata() -> None:
    profile = cast(Table, ImportProfile.__table__)
    mapping = cast(Table, ImportMapping.__table__)
    assert isinstance(profile.c.matching_strategy.type, JSONB)
    assert isinstance(profile.c.configuration.type, JSONB)
    assert next(iter(profile.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(profile.c.entity_type_id.foreign_keys)).ondelete == "RESTRICT"
    assert check_names(profile) == {"ck_import_profiles_source_type"}
    assert isinstance(mapping.c.transformation_config.type, JSONB)
    assert next(iter(mapping.c.import_profile_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(mapping.c.target_attribute_definition_id.foreign_keys)).ondelete == "RESTRICT"
    assert check_names(mapping) == {
        "ck_import_mappings_target",
    }


def test_jobs_preserve_staged_status_summaries_and_idempotency() -> None:
    table = cast(Table, ImportJob.__table__)
    assert isinstance(table.c.dry_run_summary.type, JSONB)
    assert isinstance(table.c.final_summary.type, JSONB)
    assert next(iter(table.c.workspace_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.import_profile_id.foreign_keys)).ondelete == "SET NULL"
    assert check_names(table) == {"ck_import_jobs_status"}
    indexes = {str(index.name): index for index in table.indexes if index.name is not None}
    assert set(indexes) == {
        "uq_import_jobs_idempotency",
    }
    assert indexes["uq_import_jobs_idempotency"].unique
    assert indexes["uq_import_jobs_idempotency"].dialect_options["postgresql"]["where"] is not None


def test_conflicts_retain_both_values_and_explicit_resolution() -> None:
    table = cast(Table, ImportConflict.__table__)
    assert isinstance(table.c.existing_value.type, JSONB)
    assert isinstance(table.c.imported_value.type, JSONB)
    assert next(iter(table.c.import_job_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(table.c.entity_id.foreign_keys)).ondelete == "SET NULL"
    assert check_names(table) == {
        "ck_import_conflicts_resolution",
    }
    assert {index.name for index in table.indexes} == {"idx_import_conflicts_job"}
