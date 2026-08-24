"""Reusable import-profile authorization and validation tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidMetadataError, PermissionDeniedError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, User
from app.models.import_job import ImportMapping, ImportProfile
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import Workspace
from app.repositories.import_profile import ImportProfileRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.import_profile import (
    CompositeMatchingStrategy,
    EntityIdMatchingStrategy,
    ImportMappingInput,
    ParentKeyMatchingStrategy,
    UniqueAttributeMatchingStrategy,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.import_profile import ImportProfileService


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()


class FakeWorkspaceRepository:
    def __init__(self, workspace: Workspace | None) -> None:
        self.workspace = workspace
        self.permissions: tuple[str, ...] = ()

    async def accessible_workspace(self, _: UUID, __: UUID) -> Workspace | None:
        return self.workspace

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return self.permissions


class FakeImportProfileRepository:
    def __init__(
        self, entity_type: EntityType, attributes: tuple[AttributeDefinition, ...]
    ) -> None:
        self.entity_type = entity_type
        self.attributes = attributes
        self.profile: ImportProfile | None = None
        self.mapping_values: list[ImportMapping] = []
        self.audit_logs: list[AuditLog] = []
        self.replaced = False

    def add_profile(self, value: ImportProfile) -> None:
        self.profile = value

    def add_mapping(self, value: ImportMapping) -> None:
        self.mapping_values.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        if self.profile is not None and not hasattr(self.profile, "created_at"):
            self.profile.created_at = datetime.now(UTC)
            self.profile.updated_at = datetime.now(UTC)

    async def entity_type_in_workspace(
        self, entity_type_id: UUID, workspace_id: UUID
    ) -> EntityType | None:
        if self.entity_type.id == entity_type_id and self.entity_type.workspace_id == workspace_id:
            return self.entity_type
        return None

    async def active_attributes(
        self, entity_type_id: UUID, ids: frozenset[UUID]
    ) -> tuple[AttributeDefinition, ...]:
        return tuple(
            item
            for item in self.attributes
            if item.entity_type_id == entity_type_id and item.id in ids
        )

    async def accessible_profile(self, profile_id: UUID, _: UUID) -> ImportProfile | None:
        return self.profile if self.profile is not None and self.profile.id == profile_id else None

    async def mappings(self, _: UUID) -> tuple[ImportMapping, ...]:
        return tuple(self.mapping_values)

    async def replace_mappings(self, _: UUID) -> None:
        self.replaced = True
        self.mapping_values.clear()


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="importer",
        email="importer@example.test",
        password_hash="unused-import-test",  # noqa: S106
        display_name="Importer",
    )
    return AuthenticatedIdentity(
        user=user, roles=("ANALYST",), permissions=tuple(item.value for item in permissions)
    )


def service(
    actor: AuthenticatedIdentity,
    workspace: Workspace,
) -> tuple[ImportProfileService, FakeImportProfileRepository, AttributeDefinition]:
    entity_type = EntityType(
        id=uuid4(),
        workspace_id=workspace.id,
        key="item",
        name="Item",
        configuration={},
        created_by=actor.user.id,
        is_active=True,
        version=1,
    )
    attribute = AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type.id,
        key="code",
        label="Code",
        data_type="TEXT",
        validation_config={},
        display_config={},
        inheritance_config={},
        display_order=0,
        is_active=True,
        version=1,
    )
    repository = FakeImportProfileRepository(entity_type, (attribute,))
    result = ImportProfileService(cast(AsyncSession, FakeSession()), actor)
    result.repository = cast(ImportProfileRepository, repository)
    result.workspace_repository = cast(WorkspaceRepository, FakeWorkspaceRepository(workspace))
    return result, repository, attribute


def mapping(attribute_id: UUID) -> ImportMappingInput:
    return ImportMappingInput(
        source_column="Code", target_attribute_definition_id=attribute_id, display_order=0
    )


def unique_strategy(attribute_id: UUID) -> UniqueAttributeMatchingStrategy:
    return UniqueAttributeMatchingStrategy.model_validate(
        {
            "type": "UNIQUE_ATTRIBUTE",
            "key": {
                "source_column": "Code",
                "attribute_definition_id": str(attribute_id),
            },
        }
    )


def audit() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


def test_mapping_requires_exactly_one_bounded_target() -> None:
    with pytest.raises(ValidationError):
        ImportMappingInput(source_column="Name")
    with pytest.raises(ValidationError):
        ImportMappingInput(
            source_column="Name",
            target_attribute_definition_id=uuid4(),
            target_system_field="name",
        )
    with pytest.raises(ValidationError):
        ImportMappingInput(source_column="Name", target_system_field="created_by")


@pytest.mark.asyncio
async def test_create_profile_validates_workspace_targets_and_audits_atomically() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, attribute = service(actor, workspace)

    result = await import_service.create_profile(
        workspace.id,
        entity_type_id=repository.entity_type.id,
        name="Items",
        description=None,
        source_type="CSV",
        matching_strategy=unique_strategy(attribute.id),
        configuration={},
        mappings=(mapping(attribute.id),),
        audit=audit(),
    )

    assert result.profile.workspace_id == workspace.id
    assert result.profile.created_by == actor.user.id
    assert result.mappings[0].target_attribute_definition_id == attribute.id
    assert repository.audit_logs[0].action == "IMPORT_PROFILE_CREATED"


@pytest.mark.asyncio
async def test_workspace_role_permission_is_effective() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, attribute = service(actor, workspace)
    workspace_repository = cast(FakeWorkspaceRepository, import_service.workspace_repository)
    workspace_repository.permissions = (PermissionCode.IMPORT_EXECUTE.value,)

    await import_service.create_profile(
        workspace.id,
        entity_type_id=repository.entity_type.id,
        name="Items",
        description=None,
        source_type="CSV",
        matching_strategy=unique_strategy(attribute.id),
        configuration={},
        mappings=(mapping(attribute.id),),
        audit=audit(),
    )
    assert repository.profile is not None


@pytest.mark.asyncio
async def test_missing_permission_is_rejected() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, _ = service(actor, workspace)
    with pytest.raises(PermissionDeniedError):
        await import_service.create_profile(
            workspace.id,
            entity_type_id=repository.entity_type.id,
            name="Items",
            description=None,
            source_type="CSV",
            matching_strategy=unique_strategy(uuid4()),
            configuration={},
            mappings=(),
            audit=audit(),
        )


@pytest.mark.asyncio
async def test_foreign_or_wrong_type_attribute_is_rejected() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, _ = service(actor, workspace)
    with pytest.raises(InvalidMetadataError):
        await import_service.create_profile(
            workspace.id,
            entity_type_id=repository.entity_type.id,
            name="Items",
            description=None,
            source_type="CSV",
            matching_strategy=unique_strategy(uuid4()),
            configuration={},
            mappings=(mapping(uuid4()),),
            audit=audit(),
        )


@pytest.mark.asyncio
async def test_mapping_replacement_is_atomic_and_audited() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, attribute = service(actor, workspace)
    created = await import_service.create_profile(
        workspace.id,
        entity_type_id=repository.entity_type.id,
        name="Items",
        description=None,
        source_type="CSV",
        matching_strategy=unique_strategy(attribute.id),
        configuration={},
        mappings=(mapping(attribute.id),),
        audit=audit(),
    )
    replacement = ImportMappingInput(source_column="Name", target_system_field="name")
    replacement_strategy = UniqueAttributeMatchingStrategy.model_validate(
        {
            "type": "UNIQUE_ATTRIBUTE",
            "key": {"source_column": "Name", "system_field": "name"},
        }
    )
    updated = await import_service.update_profile(
        created.profile.id,
        values={"name": "Updated"},
        mappings=(replacement,),
        matching_strategy=replacement_strategy,
        audit=audit(),
    )
    assert repository.replaced
    assert updated.profile.name == "Updated"
    assert updated.mappings[0].target_system_field == "name"
    assert repository.audit_logs[-1].action == "IMPORT_PROFILE_UPDATED"


def test_composite_strategy_requires_distinct_keys() -> None:
    with pytest.raises(ValidationError):
        CompositeMatchingStrategy.model_validate(
            {
                "type": "COMPOSITE_KEY",
                "keys": [
                    {"source_column": "Code", "system_field": "name"},
                    {"source_column": "Code", "attribute_definition_id": str(uuid4())},
                ],
            }
        )


@pytest.mark.asyncio
async def test_parent_and_key_requires_explicit_parent_mapping() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    import_service, repository, attribute = service(actor, workspace)
    strategy = ParentKeyMatchingStrategy.model_validate(
        {
            "type": "PARENT_AND_KEY",
            "parent_source_column": "Parent ID",
            "key": {
                "source_column": "Code",
                "attribute_definition_id": str(attribute.id),
            },
        }
    )
    with pytest.raises(InvalidMetadataError) as raised:
        await import_service.create_profile(
            workspace.id,
            entity_type_id=repository.entity_type.id,
            name="Items",
            description=None,
            source_type="CSV",
            matching_strategy=strategy,
            configuration={},
            mappings=(mapping(attribute.id),),
            audit=audit(),
        )
    assert raised.value.details["reason"] == "parent_not_mapped"


@pytest.mark.asyncio
async def test_entity_id_composite_and_parent_key_modes_are_supported() -> None:
    actor = identity(PermissionCode.IMPORT_EXECUTE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)

    entity_id_service, entity_id_repository, _ = service(actor, workspace)
    entity_id_result = await entity_id_service.create_profile(
        workspace.id,
        entity_type_id=entity_id_repository.entity_type.id,
        name="By ID",
        description=None,
        source_type="CSV",
        matching_strategy=EntityIdMatchingStrategy(type="ENTITY_ID", source_column="Entity ID"),
        configuration={},
        mappings=(),
        audit=audit(),
    )
    assert entity_id_result.profile.matching_strategy["type"] == "ENTITY_ID"

    composite_service, composite_repository, composite_attribute = service(actor, workspace)
    name_mapping = ImportMappingInput(source_column="Name", target_system_field="name")
    composite = CompositeMatchingStrategy.model_validate(
        {
            "type": "COMPOSITE_KEY",
            "keys": [
                {
                    "source_column": "Code",
                    "attribute_definition_id": str(composite_attribute.id),
                },
                {"source_column": "Name", "system_field": "name"},
            ],
        }
    )
    composite_result = await composite_service.create_profile(
        workspace.id,
        entity_type_id=composite_repository.entity_type.id,
        name="Composite",
        description=None,
        source_type="CSV",
        matching_strategy=composite,
        configuration={},
        mappings=(mapping(composite_attribute.id), name_mapping),
        audit=audit(),
    )
    assert composite_result.profile.matching_strategy["type"] == "COMPOSITE_KEY"

    parent_service, parent_repository, parent_attribute = service(actor, workspace)
    parent_mapping = ImportMappingInput(source_column="Parent ID", target_system_field="parent_id")
    parent_strategy = ParentKeyMatchingStrategy.model_validate(
        {
            "type": "PARENT_AND_KEY",
            "parent_source_column": "Parent ID",
            "key": {
                "source_column": "Code",
                "attribute_definition_id": str(parent_attribute.id),
            },
        }
    )
    parent_result = await parent_service.create_profile(
        workspace.id,
        entity_type_id=parent_repository.entity_type.id,
        name="Parent and key",
        description=None,
        source_type="CSV",
        matching_strategy=parent_strategy,
        configuration={},
        mappings=(mapping(parent_attribute.id), parent_mapping),
        audit=audit(),
    )
    assert parent_result.profile.matching_strategy["type"] == "PARENT_AND_KEY"
