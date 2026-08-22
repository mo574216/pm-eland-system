"""Generic entity creation authorization, validation, and audit tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceNotFoundError,
    StaleVersionError,
)
from app.core.permissions import PermissionCode
from app.models.entity import EntityObject
from app.models.identity import AuditLog, User
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import Workspace
from app.repositories.entity import EntityRecord, EntityRepository
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.entity import EntityService
from app.services.metadata_validation import MetadataValueValidator


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
        username="analyst",
        email="analyst@example.test",
        password_hash="unused-in-entity-test",  # noqa: S106
        display_name="Analyst",
    )
    return AuthenticatedIdentity(
        user, ("ANALYST",), tuple(permission.value for permission in permissions)
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
    def __init__(
        self, entity_type: EntityType | None, definitions: tuple[AttributeDefinition, ...]
    ) -> None:
        self.entity_type = entity_type
        self.definitions = definitions

    async def entity_type_in_workspace(self, _: UUID, __: UUID) -> EntityType | None:
        return self.entity_type

    async def list_attributes(self, _: UUID) -> tuple[AttributeDefinition, ...]:
        return self.definitions


class FakeEntityRepository:
    def __init__(self) -> None:
        self.parent: EntityObject | None = None
        self.entities: list[EntityObject] = []
        self.audit_logs: list[AuditLog] = []
        self.search: str | None = None
        self.updated: EntityObject | None = None
        self.fail_mutation = False

    def add_entity(self, entity: EntityObject) -> None:
        self.entities.append(entity)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.audit_logs.append(audit_log)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for entity in self.entities:
            entity.created_at = now
            entity.updated_at = now

    async def entity_in_workspace(self, _: UUID, __: UUID) -> EntityObject | None:
        return self.parent

    async def accessible_entity_record(self, _: UUID, __: UUID) -> EntityRecord | None:
        if self.parent is None:
            return None
        return EntityRecord(self.parent, entity_type(self.parent.workspace_id))

    async def update_entity(
        self, _: UUID, __: int, values: dict[str, object]
    ) -> EntityObject | None:
        if self.fail_mutation:
            return None
        target = self.updated if self.updated is not None else self.parent
        if target is not None:
            for key, value in values.items():
                setattr(target, key, value)
            target.version += 1
        return target

    async def archive_entity(self, _: UUID, __: int, updated_by: UUID) -> EntityObject | None:
        target = self.updated if self.updated is not None else self.parent
        if target is not None:
            target.status = "ARCHIVED"
            target.updated_by = updated_by
            target.version += 1
        return target

    async def list_entities(
        self, *_: object, **values: object
    ) -> tuple[tuple[EntityRecord, ...], int]:
        self.search = cast(str | None, values.get("search"))
        items = (
            (EntityRecord(self.parent, entity_type(self.parent.workspace_id)),)
            if self.parent is not None
            else ()
        )
        return items, len(items)


def entity_type(workspace_id: UUID) -> EntityType:
    return EntityType(
        id=uuid4(),
        workspace_id=workspace_id,
        key="business_process",
        name="Business Process",
        configuration={},
        is_active=True,
    )


def definition(entity_type_id: UUID) -> AttributeDefinition:
    return AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type_id,
        key="risk",
        label="Risk",
        data_type="TEXT",
        is_required=True,
        is_read_only=False,
        validation_config={},
        display_config={},
        inheritance_config={},
        is_active=True,
    )


def build_service(
    actor: AuthenticatedIdentity,
    workspace: Workspace | None,
    metadata: FakeMetadataRepository,
) -> tuple[EntityService, FakeWorkspaceRepository, FakeEntityRepository]:
    result = EntityService(cast(AsyncSession, FakeSession()), actor)
    workspace_repository = FakeWorkspaceRepository(workspace)
    entity_repository = FakeEntityRepository()
    result.workspace_repository = cast(WorkspaceRepository, workspace_repository)
    result.metadata_repository = cast(MetadataRepository, metadata)
    result.repository = cast(EntityRepository, entity_repository)
    result.validator = MetadataValueValidator()
    return result, workspace_repository, entity_repository


def audit_context() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_create_entity_validates_metadata_and_writes_audit_atomically() -> None:
    actor = identity(PermissionCode.ENTITY_CREATE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, repository = build_service(
        actor,
        workspace,
        FakeMetadataRepository(entity_type_value, (definition(entity_type_value.id),)),
    )

    created = await service.create_entity(
        workspace.id,
        entity_type_id=entity_type_value.id,
        parent_id=None,
        name="Permit Approval",
        description=None,
        attributes={"risk": "high"},
        audit=audit_context(),
    )

    assert created.entity.attributes == {"risk": "high"}
    assert created.entity.created_by == actor.user.id
    assert repository.audit_logs[0].action == "ENTITY_CREATED"


@pytest.mark.asyncio
async def test_required_dynamic_attribute_is_enforced() -> None:
    actor = identity(PermissionCode.ENTITY_CREATE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, repository = build_service(
        actor,
        workspace,
        FakeMetadataRepository(entity_type_value, (definition(entity_type_value.id),)),
    )

    with pytest.raises(InvalidMetadataError):
        await service.create_entity(
            workspace.id,
            entity_type_id=entity_type_value.id,
            parent_id=None,
            name="Invalid",
            description=None,
            attributes={},
            audit=audit_context(),
        )

    assert repository.entities == []
    assert repository.audit_logs == []


@pytest.mark.asyncio
async def test_workspace_role_can_supply_entity_create_permission() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, workspace_repository, repository = build_service(
        actor, workspace, FakeMetadataRepository(entity_type_value, ())
    )
    workspace_repository.permissions = (PermissionCode.ENTITY_CREATE.value,)

    await service.create_entity(
        workspace.id,
        entity_type_id=entity_type_value.id,
        parent_id=None,
        name="Application",
        description=None,
        attributes={},
        audit=audit_context(),
    )

    assert len(repository.entities) == 1


@pytest.mark.asyncio
async def test_missing_permission_and_cross_workspace_parent_are_rejected() -> None:
    actor = identity()
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, _ = build_service(actor, workspace, FakeMetadataRepository(entity_type_value, ()))
    with pytest.raises(PermissionDeniedError):
        await service.create_entity(
            workspace.id,
            entity_type_id=entity_type_value.id,
            parent_id=uuid4(),
            name="Denied",
            description=None,
            attributes={},
            audit=audit_context(),
        )

    permitted = identity(PermissionCode.ENTITY_CREATE)
    service, _, _ = build_service(
        permitted, workspace, FakeMetadataRepository(entity_type_value, ())
    )
    with pytest.raises(ResourceNotFoundError):
        await service.create_entity(
            workspace.id,
            entity_type_id=entity_type_value.id,
            parent_id=uuid4(),
            name="Invalid parent",
            description=None,
            attributes={},
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_read_requires_permission_and_normalizes_persian_search() -> None:
    actor = identity(PermissionCode.ENTITY_READ)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, repository = build_service(
        actor, workspace, FakeMetadataRepository(entity_type_value, ())
    )
    repository.parent = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_value.id,
        name="فرایند",
        status="ACTIVE",
        attributes={},
    )

    assert (await service.get_entity(repository.parent.id)).entity is repository.parent
    items, total = await service.list_entities(
        workspace.id,
        page=1,
        page_size=50,
        status=None,
        entity_type_id=None,
        parent_id=None,
        search="  \u0641\u0631\u0627\u064a\u0646\u062f\u200c  ",
    )

    assert tuple(item.entity for item in items) == (repository.parent,)
    assert total == 1
    assert repository.search == "\u0641\u0631\u0627\u06cc\u0646\u062f"


@pytest.mark.asyncio
async def test_update_merges_valid_attributes_and_audits_before_after() -> None:
    actor = identity(PermissionCode.ENTITY_UPDATE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, repository = build_service(
        actor,
        workspace,
        FakeMetadataRepository(entity_type_value, (definition(entity_type_value.id),)),
    )
    repository.parent = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_value.id,
        name="Old",
        status="ACTIVE",
        attributes={"risk": "low", "preserved": 1},
        version=3,
    )

    updated = await service.update_entity(
        repository.parent.id,
        expected_version=3,
        values={"name": "New", "attributes": {"risk": "high"}},
        audit=audit_context(),
    )

    assert updated.entity.name == "New"
    assert updated.entity.attributes == {"risk": "high", "preserved": 1}
    assert repository.audit_logs[-1].action == "ENTITY_UPDATED"
    assert repository.audit_logs[-1].before_state is not None
    assert repository.audit_logs[-1].after_state is not None


@pytest.mark.asyncio
async def test_archive_requires_permission_and_is_audited() -> None:
    actor = identity(PermissionCode.ENTITY_ARCHIVE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, repository = build_service(
        actor, workspace, FakeMetadataRepository(entity_type_value, ())
    )
    repository.parent = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_value.id,
        name="Archive me",
        status="ACTIVE",
        attributes={},
        version=2,
    )

    await service.archive_entity(repository.parent.id, expected_version=2, audit=audit_context())

    assert repository.parent.status == "ARCHIVED"
    assert repository.audit_logs[-1].action == "ENTITY_ARCHIVED"


@pytest.mark.asyncio
async def test_stale_update_is_rejected_without_an_audit() -> None:
    actor = identity(PermissionCode.ENTITY_UPDATE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    entity_type_value = entity_type(workspace.id)
    service, _, repository = build_service(
        actor, workspace, FakeMetadataRepository(entity_type_value, ())
    )
    repository.parent = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_value.id,
        name="Current",
        status="ACTIVE",
        attributes={},
        version=4,
    )
    repository.fail_mutation = True

    with pytest.raises(StaleVersionError):
        await service.update_entity(
            repository.parent.id,
            expected_version=3,
            values={"name": "Stale"},
            audit=audit_context(),
        )

    assert repository.audit_logs == []
