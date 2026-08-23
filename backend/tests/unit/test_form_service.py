"""Draft form authorization, metadata validation, immutability, and audit tests."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidMetadataError, ResourceConflictError
from app.core.permissions import PermissionCode
from app.models.form import FormDefinition, FormField
from app.models.identity import AuditLog, User
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import Workspace
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
        self.forms: list[FormDefinition] = []
        self.fields: list[FormField] = []
        self.audit_logs: list[AuditLog] = []
        self.existing_field: FormField | None = None

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

    async def update_draft_form(self, _: UUID, values: dict[str, object]) -> FormDefinition | None:
        if self.form is None or self.form.lifecycle_status != "DRAFT":
            return None
        for key, value in values.items():
            setattr(self.form, key, value)
        return self.form

    async def field_by_key(self, _: UUID, __: str) -> FormField | None:
        return self.existing_field

    async def attribute_in_workspace(
        self, _: UUID, __: UUID
    ) -> tuple[AttributeDefinition, EntityType] | None:
        return self.attribute_record


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

    with pytest.raises(InvalidMetadataError):
        await service.add_field(repository.form.id, values=values, audit=audit_context())

    values["field_type"] = "ENUM"
    created = await service.add_field(repository.form.id, values=values, audit=audit_context())
    assert created.attribute_definition_id == attribute.id
    assert repository.audit_logs[0].action == "FORM_FIELD_CREATED"
