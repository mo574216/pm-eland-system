"""Relationship authorization, constraints, duplicate policy, and audit tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidRelationshipError, ResourceNotFoundError
from app.core.permissions import PermissionCode
from app.models.entity import EntityObject
from app.models.identity import AuditLog, User
from app.models.metadata import EntityType
from app.models.relationship import EntityRelationship, RelationshipType
from app.models.workspace import Workspace
from app.repositories.relationship import RelationshipRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.relationship import RelationshipCreate, RelationshipTypeCreate
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.relationship import RelationshipService


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
        username="relationship-manager",
        email="relationship@example.test",
        password_hash="unused-in-relationship-test",  # noqa: S106
        display_name="Relationship Manager",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("ANALYST",),
        permissions=tuple(permission.value for permission in permissions),
    )


class FakeWorkspaceRepository:
    def __init__(self, workspace: Workspace | None) -> None:
        self.workspace = workspace

    async def accessible_workspace(self, _: UUID, __: UUID) -> Workspace | None:
        return self.workspace

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return ()


class FakeRelationshipRepository:
    def __init__(self) -> None:
        self.relationship_type: RelationshipType | None = None
        self.entity_type: EntityType | None = None
        self.entities: dict[UUID, EntityObject] = {}
        self.relationships: list[EntityRelationship] = []
        self.relationship_types: list[RelationshipType] = []
        self.audit_logs: list[AuditLog] = []
        self.duplicate = False
        self.deleted: EntityRelationship | None = None
        self.locks: list[UUID] = []

    def add_relationship_type(self, value: RelationshipType) -> None:
        self.relationship_types.append(value)

    def add_relationship(self, value: EntityRelationship) -> None:
        self.relationships.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for type_value in self.relationship_types:
            type_value.created_at = now
        for relationship_value in self.relationships:
            relationship_value.created_at = now

    async def acquire_workspace_lock(self, workspace_id: UUID) -> None:
        self.locks.append(workspace_id)

    async def relationship_type_by_key(self, _: UUID, __: str) -> RelationshipType | None:
        return None

    async def relationship_type_in_workspace(self, _: UUID, __: UUID) -> RelationshipType | None:
        return self.relationship_type

    async def entity_type_in_workspace(self, _: UUID, __: UUID) -> EntityType | None:
        return self.entity_type

    async def entity_in_workspace(self, entity_id: UUID, workspace_id: UUID) -> EntityObject | None:
        value = self.entities.get(entity_id)
        return value if value is not None and value.workspace_id == workspace_id else None

    async def duplicate_exists(self, *_: object) -> bool:
        return self.duplicate

    async def accessible_relationship(self, _: UUID, __: UUID) -> EntityRelationship | None:
        return self.deleted

    async def soft_delete_relationship(self, _: UUID) -> EntityRelationship | None:
        if self.deleted is not None:
            self.deleted.deleted_at = datetime.now(UTC)
        return self.deleted


def build_service(
    actor: AuthenticatedIdentity, workspace: Workspace | None
) -> tuple[RelationshipService, FakeRelationshipRepository]:
    result = RelationshipService(cast(AsyncSession, FakeSession()), actor)
    repository = FakeRelationshipRepository()
    result.workspace_repository = cast(WorkspaceRepository, FakeWorkspaceRepository(workspace))
    result.repository = cast(RelationshipRepository, repository)
    return result, repository


def audit_context() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


def entity(workspace_id: UUID, entity_type_id: UUID) -> EntityObject:
    return EntityObject(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type_id,
        name="Node",
        status="ACTIVE",
        attributes={},
        version=1,
    )


def relationship_type(
    workspace_id: UUID, *, source_type_id: UUID | None = None
) -> RelationshipType:
    return RelationshipType(
        id=uuid4(),
        workspace_id=workspace_id,
        key="uses",
        name="Uses",
        directionality="DIRECTED",
        source_type_id=source_type_id,
        target_type_id=None,
        configuration={},
        is_active=True,
    )


def test_relationship_requests_reject_unstable_keys_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        RelationshipTypeCreate(key="Uses Link", name="Uses")
    with pytest.raises(ValidationError):
        RelationshipCreate(
            relationship_type_id=uuid4(),
            source_entity_id=uuid4(),
            target_entity_id=uuid4(),
            unexpected=True,  # type: ignore[call-arg]
        )


@pytest.mark.asyncio
async def test_create_relationship_type_validates_scoped_types_and_audits() -> None:
    actor = identity(PermissionCode.METADATA_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    allowed_type = EntityType(
        id=uuid4(), workspace_id=workspace.id, key="node", name="Node", is_active=True
    )
    repository.entity_type = allowed_type

    created = await service.create_relationship_type(
        workspace.id,
        values={
            "key": "uses",
            "name": "Uses",
            "directionality": "DIRECTED",
            "source_type_id": allowed_type.id,
            "target_type_id": None,
            "configuration": {},
        },
        audit=audit_context(),
    )

    assert created.source_type_id == allowed_type.id
    assert repository.audit_logs[0].action == "RELATIONSHIP_TYPE_CREATED"


@pytest.mark.asyncio
async def test_create_relationship_enforces_type_constraints_and_audits() -> None:
    actor = identity(PermissionCode.RELATIONSHIP_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    source_type_id, target_type_id = uuid4(), uuid4()
    source, target = entity(workspace.id, source_type_id), entity(workspace.id, target_type_id)
    repository.entities = {source.id: source, target.id: target}
    repository.relationship_type = relationship_type(workspace.id, source_type_id=source_type_id)

    created = await service.create_relationship(
        workspace.id,
        relationship_type_id=repository.relationship_type.id,
        source_entity_id=source.id,
        target_entity_id=target.id,
        attributes={"weight": 2},
        audit=audit_context(),
    )

    assert created.attributes == {"weight": 2}
    assert repository.locks == [workspace.id]
    assert repository.audit_logs[0].action == "RELATIONSHIP_CREATED"


@pytest.mark.asyncio
async def test_relationship_rejects_self_links_and_cross_workspace_targets() -> None:
    actor = identity(PermissionCode.RELATIONSHIP_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    source = entity(workspace.id, uuid4())
    repository.entities[source.id] = source
    repository.relationship_type = relationship_type(workspace.id)

    with pytest.raises(InvalidRelationshipError):
        await service.create_relationship(
            workspace.id,
            relationship_type_id=repository.relationship_type.id,
            source_entity_id=source.id,
            target_entity_id=source.id,
            attributes={},
            audit=audit_context(),
        )

    with pytest.raises(ResourceNotFoundError):
        await service.create_relationship(
            workspace.id,
            relationship_type_id=repository.relationship_type.id,
            source_entity_id=source.id,
            target_entity_id=uuid4(),
            attributes={},
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_configured_duplicate_policy_is_enforced_under_workspace_lock() -> None:
    actor = identity(PermissionCode.RELATIONSHIP_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    source, target = entity(workspace.id, uuid4()), entity(workspace.id, uuid4())
    repository.entities = {source.id: source, target.id: target}
    repository.relationship_type = relationship_type(workspace.id)
    repository.relationship_type.configuration = {"allow_duplicates": False}
    repository.duplicate = True

    with pytest.raises(InvalidRelationshipError) as captured:
        await service.create_relationship(
            workspace.id,
            relationship_type_id=repository.relationship_type.id,
            source_entity_id=source.id,
            target_entity_id=target.id,
            attributes={},
            audit=audit_context(),
        )

    assert captured.value.details == {"reason": "duplicate"}
    assert repository.locks == [workspace.id]


@pytest.mark.asyncio
async def test_delete_relationship_is_soft_and_audited() -> None:
    actor = identity(PermissionCode.RELATIONSHIP_MANAGE)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    source, target = entity(workspace.id, uuid4()), entity(workspace.id, uuid4())
    repository.deleted = EntityRelationship(
        id=uuid4(),
        workspace_id=workspace.id,
        relationship_type_id=uuid4(),
        source_entity_id=source.id,
        target_entity_id=target.id,
        attributes={},
        created_by=actor.user.id,
    )

    await service.delete_relationship(repository.deleted.id, audit=audit_context())

    assert repository.deleted.deleted_at is not None
    assert repository.audit_logs[0].action == "RELATIONSHIP_DELETED"
