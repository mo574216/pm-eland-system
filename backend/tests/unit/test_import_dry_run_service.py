"""Focused dry-run classification tests for generic import mappings."""

from uuid import uuid4

import pytest

from app.models.entity import EntityObject
from app.models.import_job import ImportJob, ImportMapping, ImportProfile
from app.models.metadata import AttributeDefinition, EntityType
from app.schemas.import_profile import UniqueAttributeMatchingStrategy
from app.services.import_dry_run import ImportDryRunService
from app.services.import_parser import ImportSourceRow
from app.services.metadata_validation import MetadataValueValidator


@pytest.mark.asyncio
async def test_dry_run_classifies_rows_persists_conflicts_and_changes_no_entity() -> None:
    workspace_id = uuid4()
    entity_type = EntityType(
        id=uuid4(),
        workspace_id=workspace_id,
        key="generic_item",
        name="Generic item",
        configuration={},
        is_active=True,
        version=1,
    )
    code = AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type.id,
        key="code",
        label="Code",
        data_type="TEXT",
        is_required=True,
        validation_config={},
        display_config={},
        inheritance_config={},
        display_order=0,
        is_active=True,
        version=1,
    )
    profile = ImportProfile(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type.id,
        name="Generic CSV",
        source_type="CSV",
        matching_strategy={},
        configuration={},
    )
    mappings = (
        ImportMapping(
            id=uuid4(),
            import_profile_id=profile.id,
            source_column="Name",
            target_system_field="name",
            transformation_config={},
            display_order=0,
        ),
        ImportMapping(
            id=uuid4(),
            import_profile_id=profile.id,
            source_column="Code",
            target_attribute_definition_id=code.id,
            transformation_config={},
            display_order=1,
        ),
    )
    existing = EntityObject(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type.id,
        name="Old name",
        status="ACTIVE",
        attributes={"code": "A"},
        version=1,
    )
    original_state = (existing.name, dict(existing.attributes), existing.version)
    rows = (
        ImportSourceRow("items.csv", 2, {"Name": "New name", "Code": "A"}),
        ImportSourceRow("items.csv", 3, {"Name": "Created", "Code": "B"}),
        ImportSourceRow("items.csv", 4, {"Name": "Duplicate", "Code": "B"}),
        ImportSourceRow("items.csv", 5, {"Name": "", "Code": "C"}),
    )
    strategy = UniqueAttributeMatchingStrategy.model_validate(
        {
            "type": "UNIQUE_ATTRIBUTE",
            "key": {"source_column": "Code", "attribute_definition_id": str(code.id)},
        }
    )
    service = object.__new__(ImportDryRunService)
    service.validator = MetadataValueValidator()
    job = ImportJob(
        id=uuid4(),
        workspace_id=workspace_id,
        import_profile_id=profile.id,
        source_object_key=f"workspaces/{workspace_id}/imports/source.csv",
        status="UPLOADED",
    )

    result, conflicts = await service._classify(
        job,
        profile,
        mappings,
        entity_type,
        (code,),
        (existing,),
        strategy,
        rows,
    )

    assert result.status == "VALIDATION_FAILED"
    assert result.summary.rows_read == 4
    assert result.summary.rows_valid == 2
    assert result.summary.rows_invalid == 2
    assert result.summary.records_to_create == 1
    assert result.summary.records_to_update == 1
    assert result.summary.records_unchanged == 0
    assert result.summary.conflicts == 1
    assert {(item.row_number, item.field, item.code) for item in result.validation_errors} == {
        (4, "matching_key", "DUPLICATE_ROW"),
        (5, "name", "REQUIRED"),
    }
    assert conflicts[0].entity_id == existing.id
    assert conflicts[0].attribute_key == "name"
    assert (existing.name, existing.attributes, existing.version) == original_state
