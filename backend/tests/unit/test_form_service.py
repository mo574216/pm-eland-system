"""Draft form authorization, metadata validation, immutability, and audit tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.permissions import PermissionCode
from app.models.entity import EntityObject
from app.models.form import FormDefinition, FormField
from app.models.identity import AuditLog, User
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import Workspace
from app.repositories.entity import EntityRepository
from app.repositories.form import FormRecord, FormRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.form import FormFieldCreate, FormUpdate
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.form import FormService


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
        username="form-designer",
        email="forms@example.test",
        password_hash="unused-in-form-test",  # noqa: S106
        display_name="Form Designer",
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("PROJECT_MANAGER",),
        permissions=tuple(permission.value for permission in permissions),
    )


class FakeWorkspaceRepository:
    def __init__(self, workspace: Workspace | None) -> None:
        self.workspace = workspace

    async def accessible_workspace(self, _: UUID, __: UUID) -> Workspace | None:
        return self.workspace

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return ()


class FakeFormRepository:
    def __init__(self) -> None:
        self.form: FormDefinition | None = None
        self.entity_type: EntityType | None = None
        self.attribute_record: tuple[AttributeDefinition, EntityType] | None = None
        self.attribute_records: dict[UUID, AttributeDefinition] = {}
        self.forms: list[FormDefinition] = []
        self.fields: list[FormField] = []
        self.audit_logs: list[AuditLog] = []
        self.existing_field: FormField | None = None
        self.workspace_locks: list[UUID] = []

    def add_form(self, value: FormDefinition) -> None:
        self.forms.append(value)

    def add_field(self, value: FormField) -> None:
        self.fields.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        now = datetime.now(UTC)
        for form_value in self.forms:
            form_value.created_at = now

    async def form_by_key(self, _: UUID, __: str) -> FormDefinition | None:
        return self.form

    async def entity_type_in_workspace(self, _: UUID, __: UUID) -> EntityType | None:
        return self.entity_type

    async def accessible_form(self, _: UUID, __: UUID) -> FormDefinition | None:
        return self.form

    async def accessible_form_record(self, _: UUID, __: UUID) -> FormRecord | None:
        return None if self.form is None else FormRecord(self.form, tuple(self.fields))

    async def lock_accessible_form(self, _: UUID, __: UUID) -> FormDefinition | None:
        return self.form

    async def list_fields(self, _: UUID) -> tuple[FormField, ...]:
        return tuple(self.fields)

    async def update_draft_form(self, _: UUID, values: dict[str, object]) -> FormDefinition | None:
        if self.form is None or self.form.lifecycle_status != "DRAFT":
            return None
        for key, value in values.items():
            setattr(self.form, key, value)
        return self.form

    async def field_by_key(self, _: UUID, __: str) -> FormField | None:
        return self.existing_field

    async def publish_draft(self, _: UUID) -> FormDefinition | None:
        if self.form is None or self.form.lifecycle_status != "DRAFT":
            return None
        self.form.lifecycle_status = "PUBLISHED"
        self.form.published_at = datetime.now(UTC)
        return self.form

    async def acquire_workspace_lock(self, workspace_id: UUID) -> None:
        self.workspace_locks.append(workspace_id)

    async def next_version_number(self, _: UUID, __: str) -> int:
        return (
            max(
                [value.version_number for value in [self.form, *self.forms] if value is not None],
                default=0,
            )
            + 1
        )

    async def attribute_in_workspace(
        self, _: UUID, __: UUID
    ) -> tuple[AttributeDefinition, EntityType] | None:
        return self.attribute_record

    async def attributes_in_workspace(
        self, attribute_ids: frozenset[UUID], _: UUID
    ) -> dict[UUID, AttributeDefinition]:
        return {
            attribute_id: self.attribute_records[attribute_id]
            for attribute_id in attribute_ids
            if attribute_id in self.attribute_records
        }


class FakeEntityRepository:
    def __init__(self, entities: tuple[EntityObject, ...] = ()) -> None:
        self.entities = {entity.id: entity for entity in entities}

    async def entity_in_workspace(self, entity_id: UUID, workspace_id: UUID) -> EntityObject | None:
        entity = self.entities.get(entity_id)
        return entity if entity is not None and entity.workspace_id == workspace_id else None

    async def entities_in_workspace(
        self, entity_ids: frozenset[UUID], workspace_id: UUID
    ) -> dict[UUID, EntityObject]:
        return {
            entity_id: entity
            for entity_id in entity_ids
            if (entity := self.entities.get(entity_id)) is not None
            and entity.workspace_id == workspace_id
        }


def build_service(
    actor: AuthenticatedIdentity, workspace: Workspace | None
) -> tuple[FormService, FakeFormRepository]:
    result = FormService(cast(AsyncSession, FakeSession()), actor)
    repository = FakeFormRepository()
    result.workspace_repository = cast(WorkspaceRepository, FakeWorkspaceRepository(workspace))
    result.repository = cast(FormRepository, repository)
    return result, repository


def audit_context() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


def form(workspace_id: UUID, actor_id: UUID, entity_type_id: UUID | None = None) -> FormDefinition:
    return FormDefinition(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=entity_type_id,
        key="process_specification",
        name="Process Specification",
        version_number=1,
        lifecycle_status="DRAFT",
        schema_json={"sections": []},
        created_by=actor_id,
    )


def test_form_payloads_reject_unknown_types_and_empty_updates() -> None:
    with pytest.raises(ValidationError):
        FormFieldCreate(key="risk", label="Risk", field_type="SCRIPT")
    with pytest.raises(ValidationError):
        FormUpdate()
    with pytest.raises(ValidationError):
        FormUpdate.model_validate(
            {
                "schema_json": {
                    "sections": [
                        {"key": "general", "label": "General"},
                        {"key": "general", "label": "Duplicate"},
                    ]
                }
            }
        )


@pytest.mark.asyncio
async def test_create_form_is_draft_version_one_and_audited() -> None:
    actor = identity(PermissionCode.FORM_DESIGN)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    entity_type = EntityType(
        id=uuid4(), workspace_id=workspace.id, key="node", name="Node", is_active=True
    )
    repository.entity_type = entity_type

    created = await service.create_form(
        workspace.id,
        values={
            "key": "process_specification",
            "name": "Process Specification",
            "entity_type_id": entity_type.id,
            "description": None,
        },
        audit=audit_context(),
    )

    assert created.form.version_number == 1
    assert created.form.lifecycle_status == "DRAFT"
    assert created.form.schema_json == {"sections": []}
    assert repository.audit_logs[0].action == "FORM_CREATED"


@pytest.mark.asyncio
async def test_published_form_cannot_be_mutated_by_draft_endpoint() -> None:
    actor = identity(PermissionCode.FORM_DESIGN)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    repository.form = form(workspace.id, actor.user.id)
    repository.form.lifecycle_status = "PUBLISHED"

    with pytest.raises(ResourceConflictError):
        await service.update_draft_form(
            repository.form.id,
            values={"name": "Changed"},
            audit=audit_context(),
        )

    with pytest.raises(ResourceConflictError):
        await service.add_field(
            repository.form.id,
            values={
                "key": "risk",
                "label": "Risk",
                "field_type": "TEXT",
                "attribute_definition_id": None,
                "section_key": None,
                "display_order": 0,
                "is_required": False,
                "is_read_only": False,
                "configuration": {},
                "visibility_rule": {},
                "validation_rule": {},
                "inheritance_rule": {},
            },
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_add_field_validates_attribute_type_and_audits() -> None:
    actor = identity(PermissionCode.FORM_DESIGN)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    entity_type = EntityType(
        id=uuid4(), workspace_id=workspace.id, key="node", name="Node", is_active=True
    )
    attribute = AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type.id,
        key="risk",
        label="Risk",
        data_type="ENUM",
        is_active=True,
    )
    repository.form = form(workspace.id, actor.user.id, entity_type.id)
    repository.form.schema_json = {
        "sections": [{"key": "general", "label": "General", "display_order": 0}]
    }
    repository.attribute_record = (attribute, entity_type)
    values: dict[str, object] = {
        "key": "risk",
        "label": "Risk",
        "field_type": "TEXT",
        "attribute_definition_id": attribute.id,
        "section_key": "general",
        "display_order": 10,
        "is_required": True,
        "is_read_only": False,
        "configuration": {},
        "visibility_rule": {},
        "validation_rule": {},
        "inheritance_rule": {},
    }

    values["visibility_rule"] = {
        "version": 1,
        "condition": {"path": "current.risk", "operator": "python_eval", "value": "x"},
    }
    with pytest.raises(InvalidMetadataError) as invalid_rule:
        await service.add_field(repository.form.id, values=values, audit=audit_context())
    assert invalid_rule.value.details == {"field": "rules", "reason": "invalid_rule"}

    values["visibility_rule"] = {}
    with pytest.raises(InvalidMetadataError):
        await service.add_field(repository.form.id, values=values, audit=audit_context())

    values["field_type"] = "ENUM"
    created = await service.add_field(repository.form.id, values=values, audit=audit_context())
    assert created.attribute_definition_id == attribute.id
    assert repository.audit_logs[0].action == "FORM_FIELD_CREATED"


def form_field(form_id: UUID) -> FormField:
    return FormField(
        id=uuid4(),
        form_definition_id=form_id,
        attribute_definition_id=None,
        key="summary",
        label="Summary",
        field_type="TEXT",
        section_key="general",
        display_order=10,
        is_required=True,
        is_read_only=False,
        configuration={"multiline": True},
        visibility_rule={},
        validation_rule={},
        inheritance_rule={},
    )


@pytest.mark.asyncio
async def test_publish_validates_definition_and_makes_it_immutable() -> None:
    actor = identity(PermissionCode.FORM_DESIGN)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    repository.form = form(workspace.id, actor.user.id)
    repository.form.schema_json = {
        "sections": [{"key": "general", "label": "General", "display_order": 10}]
    }
    repository.fields = [form_field(repository.form.id)]

    published = await service.publish_form(repository.form.id, audit=audit_context())

    assert published.form.lifecycle_status == "PUBLISHED"
    assert published.form.published_at is not None
    assert repository.audit_logs[0].action == "FORM_PUBLISHED"
    with pytest.raises(ResourceConflictError):
        await service.update_draft_form(
            repository.form.id,
            values={"name": "Silent reinterpretation"},
            audit=audit_context(),
        )


@pytest.mark.asyncio
async def test_publish_rejects_definition_without_fields() -> None:
    actor = identity(PermissionCode.FORM_DESIGN)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    repository.form = form(workspace.id, actor.user.id)

    with pytest.raises(InvalidMetadataError) as captured:
        await service.publish_form(repository.form.id, audit=audit_context())
    assert captured.value.details == {"field": "fields", "reason": "required"}


@pytest.mark.asyncio
async def test_new_version_is_independent_draft_copy() -> None:
    actor = identity(PermissionCode.FORM_DESIGN)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    repository.form = form(workspace.id, actor.user.id)
    repository.form.lifecycle_status = "PUBLISHED"
    repository.form.schema_json = {
        "sections": [{"key": "general", "label": "General", "display_order": 10}]
    }
    repository.fields = [form_field(repository.form.id)]

    copied = await service.create_new_version(repository.form.id, audit=audit_context())

    assert copied.form.id != repository.form.id
    assert copied.form.version_number == 2
    assert copied.form.lifecycle_status == "DRAFT"
    assert copied.fields[0].id != repository.fields[0].id
    assert copied.fields[0].form_definition_id == copied.form.id
    assert repository.workspace_locks == [workspace.id]
    assert repository.audit_logs[0].action == "FORM_VERSION_CREATED"

    copied.form.schema_json["sections"] = []
    copied.fields[0].configuration["multiline"] = False
    assert repository.form.schema_json["sections"] != []
    assert repository.fields[0].configuration["multiline"] is True


def render_field(
    form_id: UUID,
    key: str,
    *,
    attribute_id: UUID | None = None,
    section_key: str | None = "general",
    field_type: str = "TEXT",
    display_order: int = 10,
    configuration: dict[str, object] | None = None,
    visibility_rule: dict[str, object] | None = None,
    validation_rule: dict[str, object] | None = None,
    inheritance_rule: dict[str, object] | None = None,
) -> FormField:
    return FormField(
        id=uuid4(),
        form_definition_id=form_id,
        attribute_definition_id=attribute_id,
        key=key,
        label=key.replace("_", " ").title(),
        field_type=field_type,
        section_key=section_key,
        display_order=display_order,
        is_required=False,
        is_read_only=False,
        configuration=configuration or {},
        visibility_rule=visibility_rule or {},
        validation_rule=validation_rule or {},
        inheritance_rule=inheritance_rule or {},
    )


@pytest.mark.asyncio
async def test_render_contract_normalizes_context_rules_values_and_sections() -> None:
    actor = identity(PermissionCode.ENTITY_READ)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    entity_type_id = uuid4()
    parent = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_id,
        name="Parent Service",
        status="ACTIVE",
        attributes={},
    )
    reference = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_id,
        name="Referenced Owner",
        status="ACTIVE",
        attributes={},
    )
    entity = EntityObject(
        id=uuid4(),
        workspace_id=workspace.id,
        entity_type_id=entity_type_id,
        parent_id=parent.id,
        name="Current Process",
        status="ACTIVE",
        attributes={"summary_attribute": "Existing summary", "owner_ref": str(reference.id)},
    )
    service.entity_repository = cast(
        EntityRepository, FakeEntityRepository((entity, parent, reference))
    )
    repository.form = form(workspace.id, actor.user.id, entity_type_id)
    repository.form.lifecycle_status = "PUBLISHED"
    repository.form.schema_json = {
        "sections": [
            {"key": "details", "label": "Details", "display_order": 20},
            {"key": "general", "label": "General", "display_order": 10},
        ]
    }
    summary_attribute = AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type_id,
        key="summary_attribute",
        label="Summary",
        data_type="TEXT",
        default_value="Attribute default",
        is_active=True,
    )
    reference_attribute = AttributeDefinition(
        id=uuid4(),
        entity_type_id=entity_type_id,
        key="owner_ref",
        label="Owner",
        data_type="ENTITY_REFERENCE",
        is_active=True,
    )
    repository.attribute_records = {
        summary_attribute.id: summary_attribute,
        reference_attribute.id: reference_attribute,
    }
    repository.fields = [
        render_field(repository.form.id, "summary", attribute_id=summary_attribute.id),
        render_field(
            repository.form.id,
            "parent_name",
            inheritance_rule={
                "version": 1,
                "source_path": "parent.name",
                "mode": "READ_ONLY",
            },
            display_order=20,
        ),
        render_field(
            repository.form.id,
            "mitigation",
            section_key="details",
            visibility_rule={
                "version": 1,
                "condition": {"path": "current.summary", "operator": "exists"},
            },
            validation_rule={
                "version": 1,
                "required_when": {"path": "current.summary", "operator": "exists"},
            },
            inheritance_rule={
                "version": 1,
                "static_value": "Review required",
                "mode": "EDITABLE_DEFAULT",
            },
        ),
        render_field(
            repository.form.id,
            "owner_ref",
            attribute_id=reference_attribute.id,
            section_key="details",
            field_type="ENTITY_REFERENCE",
            display_order=20,
        ),
        render_field(
            repository.form.id,
            "owner_name",
            section_key="details",
            inheritance_rule={
                "version": 1,
                "source_path": "referenced.owner_ref.name",
                "mode": "READ_ONLY",
            },
            display_order=30,
        ),
        render_field(
            repository.form.id,
            "rows",
            section_key=None,
            field_type="TABLE",
            configuration={"columns": [{"key": "item", "type": "TEXT"}]},
        ),
    ]

    rendered = await service.render_form(repository.form.id, entity_id=entity.id)

    assert [section.key for section in rendered.sections] == ["general", "details", None]
    assert rendered.entity_id == entity.id
    fields = {field.key: field for section in rendered.sections for field in section.fields}
    assert fields["summary"].value == "Existing summary"
    assert fields["summary"].value_source == "CURRENT"
    assert fields["parent_name"].value == "Parent Service"
    assert fields["parent_name"].read_only is True
    assert fields["mitigation"].visible is True
    assert fields["mitigation"].required is True
    assert fields["mitigation"].value_source == "INHERITED"
    assert fields["owner_name"].value == "Referenced Owner"
    assert fields["rows"].configuration["columns"] == [{"key": "item", "type": "TEXT"}]


@pytest.mark.asyncio
async def test_render_contract_requires_design_for_draft_and_hides_foreign_entities() -> None:
    actor = identity(PermissionCode.ENTITY_READ)
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=actor.user.id)
    service, repository = build_service(actor, workspace)
    repository.form = form(workspace.id, actor.user.id, uuid4())
    repository.fields = [render_field(repository.form.id, "summary", section_key=None)]
    foreign = EntityObject(
        id=uuid4(),
        workspace_id=uuid4(),
        entity_type_id=repository.form.entity_type_id,
        name="Foreign",
        status="ACTIVE",
        attributes={},
    )
    service.entity_repository = cast(EntityRepository, FakeEntityRepository((foreign,)))

    with pytest.raises(PermissionDeniedError):
        await service.render_form(repository.form.id, entity_id=None)

    repository.form.lifecycle_status = "PUBLISHED"
    with pytest.raises(ResourceNotFoundError):
        await service.render_form(repository.form.id, entity_id=foreign.id)
