"""Entity-type lifecycle, authorization, and audit tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidMetadataError, PermissionDeniedError, StaleVersionError
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog, User
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import Workspace
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.metadata import AttributeCreate, EntityTypeCreate
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.metadata import MetadataService


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="metadata-designer",
        email="designer@example.test",
        password_hash="unused-in-metadata-test",  # noqa: S106
        display_name="Designer",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("PROJECT_MANAGER",),
        permissions=tuple(permission.value for permission in permissions),
    )


def entity_type(workspace_id: UUID, actor_id: UUID) -> EntityType:
    return EntityType(
        id=uuid4(),
        workspace_id=workspace_id,
        key="business_process",
        name="Business Process",
        plural_name="Business Processes",
        description=None,
        configuration={},
        created_by=actor_id,
        is_active=True,
        version=1,
    )


class FakeWorkspaceRepository:
    def __init__(self, workspace: Workspace | None) -> None:
        self.workspace = workspace
        self.permissions: tuple[str, ...] = ()

    async def accessible_workspace(self, _: UUID, __: UUID) -> Workspace | None:
        return self.workspace

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return self.permissions


class FakeMetadataRepository:
    def __init__(self, existing: EntityType | None = None) -> None:
        self.existing = existing
        self.entity_types: list[EntityType] = []
        self.attributes: list[AttributeDefinition] = []
        self.existing_attribute: AttributeDefinition | None = None
        self.audit_logs: list[AuditLog] = []
        self.updated: EntityType | None = existing

    def add_entity_type(self, value: EntityType) -> None:
        self.entity_types.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for entity_type_value in self.entity_types:
            entity_type_value.created_at = now
            entity_type_value.updated_at = now
        for attribute_value in self.attributes:
            attribute_value.created_at = now
            attribute_value.updated_at = now

    async def entity_type_by_key(self, _: UUID, __: str) -> EntityType | None:
        return self.existing

    async def accessible_entity_type(self, _: UUID, __: UUID) -> EntityType | None:
        return self.existing

    def add_attribute(self, value: AttributeDefinition) -> None:
        self.attributes.append(value)

    async def attribute_by_key(self, _: UUID, __: str) -> AttributeDefinition | None:
        return self.existing_attribute

    async def entity_type_in_workspace(self, _: UUID, __: UUID) -> EntityType | None:
        return self.existing

    async def list_entity_types(
        self, *_: object, **__: object
    ) -> tuple[tuple[EntityType, ...], int]:
        items = tuple(self.entity_types)
        return items, len(items)

    async def update_entity_type(
        self, _: UUID, __: int, values: dict[str, object]
    ) -> EntityType | None:
        if self.updated is not None:
            for key, value in values.items():
                setattr(self.updated, key, value)
            self.updated.version += 1
        return self.updated

    async def archive_entity_type(self, _: UUID, __: int) -> EntityType | None:
        if self.updated is not None:
            self.updated.is_active = False
            self.updated.version += 1
        return self.updated


def service(
    actor: AuthenticatedIdentity,
    workspace: Workspace | None,
    repository: FakeMetadataRepository,
) -> tuple[MetadataService, FakeWorkspaceRepository]:
    result = MetadataService(cast(AsyncSession, FakeSession()), actor)
    workspace_repository = FakeWorkspaceRepository(workspace)
    result.repository = cast(MetadataRepository, repository)
    result.workspace_repository = cast(WorkspaceRepository, workspace_repository)
    return result, workspace_repository


def audit_context() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


def test_entity_type_key_requires_stable_lower_snake_case() -> None:
    with pytest.raises(ValidationError):
        EntityTypeCreate(key="Business Process", name="Business Process")


@pytest.mark.asyncio
async def test_create_entity_type_is_audited_atomically() -> None:
    actor = identity(PermissionCode.METADATA_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    repository = FakeMetadataRepository()
    metadata_service, _ = service(actor, workspace, repository)

    created = await metadata_service.create_entity_type(
        workspace.id,
        values={"key": "business_process", "name": "Business Process", "configuration": {}},
        audit=audit_context(),
    )

    assert created.workspace_id == workspace.id
    assert created.created_by == actor.user.id
    assert repository.audit_logs[0].action == "ENTITY_TYPE_CREATED"


@pytest.mark.asyncio
async def test_workspace_role_can_supply_metadata_manage_permission() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    repository = FakeMetadataRepository()
    metadata_service, workspace_repository = service(actor, workspace, repository)
    workspace_repository.permissions = (PermissionCode.METADATA_MANAGE.value,)

    await metadata_service.create_entity_type(
        workspace.id,
        values={"key": "application", "name": "Application", "configuration": {}},
        audit=audit_context(),
    )

    assert len(repository.entity_types) == 1


@pytest.mark.asyncio
async def test_metadata_mutation_rejects_missing_permission() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    metadata_service, _ = service(actor, workspace, FakeMetadataRepository())

    with pytest.raises(PermissionDeniedError):
        await metadata_service.create_entity_type(
            workspace.id,
            values={"key": "application", "name": "Application", "configuration": {}},
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_stale_update_does_not_write_audit() -> None:
    actor = identity(PermissionCode.METADATA_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    existing = entity_type(workspace.id, actor.user.id)
    repository = FakeMetadataRepository(existing)
    repository.updated = None
    metadata_service, _ = service(actor, workspace, repository)

    with pytest.raises(StaleVersionError):
        await metadata_service.update_entity_type(
            existing.id,
            expected_version=99,
            values={"name": "Changed"},
            audit=audit_context(),
        )

    assert repository.audit_logs == []


def test_unsupported_attribute_type_is_rejected_at_api_boundary() -> None:
    with pytest.raises(ValidationError):
        AttributeCreate(key="risk", label="Risk", data_type="DOMAIN_RISK")


@pytest.mark.asyncio
async def test_enum_requires_nonempty_unique_options() -> None:
    actor = identity(PermissionCode.METADATA_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    existing = entity_type(workspace.id, actor.user.id)
    metadata_service, _ = service(actor, workspace, FakeMetadataRepository(existing))

    with pytest.raises(InvalidMetadataError):
        await metadata_service.create_attribute(
            existing.id,
            values=AttributeCreate(key="risk", label="Risk", data_type="ENUM").model_dump(),
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_valid_enum_attribute_is_created_and_audited() -> None:
    actor = identity(PermissionCode.METADATA_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    existing = entity_type(workspace.id, actor.user.id)
    repository = FakeMetadataRepository(existing)
    metadata_service, _ = service(actor, workspace, repository)

    created = await metadata_service.create_attribute(
        existing.id,
        values=AttributeCreate(
            key="risk",
            label="Risk",
            data_type="ENUM",
            display_config={
                "options": [
                    {"value": "LOW", "label": "Low"},
                    {"value": "HIGH", "label": "High"},
                ]
            },
        ).model_dump(),
        audit=audit_context(),
    )

    assert created.entity_type_id == existing.id
    assert repository.audit_logs[-1].action == "ATTRIBUTE_DEFINITION_CREATED"


@pytest.mark.asyncio
async def test_invalid_inheritance_reference_is_rejected() -> None:
    actor = identity(PermissionCode.METADATA_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    existing = entity_type(workspace.id, actor.user.id)
    metadata_service, _ = service(actor, workspace, FakeMetadataRepository(existing))

    with pytest.raises(InvalidMetadataError):
        await metadata_service.create_attribute(
            existing.id,
            values=AttributeCreate(
                key="inherited_owner",
                label="Inherited owner",
                data_type="TEXT",
                inheritance_config={
                    "source": {"scope": "parent", "attribute": "owner"},
                    "mode": "read_only",
                },
            ).model_dump(),
            audit=audit_context(),
        )
