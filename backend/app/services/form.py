"""Draft form definition authorization, validation, and audit service."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.form import FormDefinition, FormField
from app.models.identity import AuditLog
from app.repositories.form import FormRecord, FormRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.form_rules import FormRuleEvaluator, InvalidFormRuleError


class FormService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.workspace_repository = WorkspaceRepository(session)
        self.repository = FormRepository(session)
        self.rule_evaluator = FormRuleEvaluator()

    async def _require_permission(self, workspace_id: UUID, permission: PermissionCode) -> None:
        workspace = await self.workspace_repository.accessible_workspace(
            workspace_id, self.actor.user.id
        )
        if workspace is None:
            raise WorkspaceAccessDeniedError
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if permission.value not in effective:
            raise PermissionDeniedError

    async def create_form(
        self,
        workspace_id: UUID,
        *,
        values: dict[str, object],
        audit: AuditContext,
    ) -> FormRecord:
        async with self.session.begin():
            await self._require_permission(workspace_id, PermissionCode.FORM_DESIGN)
            key = str(values["key"])
            if await self.repository.form_by_key(workspace_id, key) is not None:
                raise ResourceConflictError
            await self._validate_entity_type(workspace_id, values.get("entity_type_id"))
            form = FormDefinition(
                id=uuid4(),
                workspace_id=workspace_id,
                version_number=1,
                lifecycle_status="DRAFT",
                schema_json={"sections": []},
                created_by=self.actor.user.id,
                **values,
            )
            self.repository.add_form(form)
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    workspace_id,
                    "FORM_CREATED",
                    "form_definition",
                    form.id,
                    None,
                    self._form_state(form),
                )
            )
            await self.repository.flush()
        return FormRecord(form, ())

    async def list_forms(
        self,
        workspace_id: UUID,
        *,
        entity_type_id: UUID | None,
        lifecycle_status: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[tuple[FormDefinition, ...], int]:
        await self._require_permission(workspace_id, PermissionCode.ENTITY_READ)
        if entity_type_id is not None:
            await self._validate_entity_type(workspace_id, entity_type_id)
        return await self.repository.list_forms(
            workspace_id,
            self.actor.user.id,
            entity_type_id=entity_type_id,
            lifecycle_status=lifecycle_status,
            search=search,
            page=page,
            page_size=page_size,
        )

    async def get_form(self, form_id: UUID) -> FormRecord:
        record = await self.repository.accessible_form_record(form_id, self.actor.user.id)
        if record is None:
            raise ResourceNotFoundError
        await self._require_permission(record.form.workspace_id, PermissionCode.ENTITY_READ)
        return record

    async def update_draft_form(
        self,
        form_id: UUID,
        *,
        values: dict[str, object],
        audit: AuditContext,
    ) -> FormRecord:
        async with self.session.begin():
            record = await self.repository.accessible_form_record(form_id, self.actor.user.id)
            if record is None:
                raise ResourceNotFoundError
            form = record.form
            await self._require_permission(form.workspace_id, PermissionCode.FORM_DESIGN)
            if form.lifecycle_status != "DRAFT":
                raise ResourceConflictError
            if "entity_type_id" in values:
                await self._validate_entity_type(form.workspace_id, values.get("entity_type_id"))
            before_state = self._form_state(form)
            updated = await self.repository.update_draft_form(form_id, values)
            if updated is None:
                raise ResourceConflictError
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    updated.workspace_id,
                    "FORM_UPDATED",
                    "form_definition",
                    updated.id,
                    before_state,
                    self._form_state(updated),
                )
            )
        return FormRecord(updated, record.fields)

    async def add_field(
        self,
        form_id: UUID,
        *,
        values: dict[str, object],
        audit: AuditContext,
    ) -> FormField:
        async with self.session.begin():
            form = await self.repository.accessible_form(form_id, self.actor.user.id)
            if form is None:
                raise ResourceNotFoundError
            await self._require_permission(form.workspace_id, PermissionCode.FORM_DESIGN)
            if form.lifecycle_status != "DRAFT":
                raise ResourceConflictError
            key = str(values["key"])
            if await self.repository.field_by_key(form.id, key) is not None:
                raise ResourceConflictError
            section_key = values.get("section_key")
            if section_key is not None and section_key not in self._section_keys(form):
                raise InvalidMetadataError({"field": "section_key", "reason": "not_found"})
            try:
                self.rule_evaluator.validate_rules(
                    visibility_rule=self._rule_mapping(values.get("visibility_rule")),
                    validation_rule=self._rule_mapping(values.get("validation_rule")),
                    inheritance_rule=self._rule_mapping(values.get("inheritance_rule")),
                )
            except InvalidFormRuleError as error:
                raise InvalidMetadataError({"field": "rules", "reason": "invalid_rule"}) from error
            attribute_id = values.get("attribute_definition_id")
            if attribute_id is not None:
                if not isinstance(attribute_id, UUID):
                    raise InvalidMetadataError
                attribute_record = await self.repository.attribute_in_workspace(
                    attribute_id, form.workspace_id
                )
                if attribute_record is None:
                    raise InvalidMetadataError(
                        {"field": "attribute_definition_id", "reason": "not_found"}
                    )
                attribute, entity_type = attribute_record
                if form.entity_type_id is not None and entity_type.id != form.entity_type_id:
                    raise InvalidMetadataError(
                        {"field": "attribute_definition_id", "reason": "wrong_entity_type"}
                    )
                if attribute.data_type != values["field_type"]:
                    raise InvalidMetadataError(
                        {"field": "field_type", "reason": "attribute_type_mismatch"}
                    )
            field = FormField(id=uuid4(), form_definition_id=form.id, **values)
            self.repository.add_field(field)
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    form.workspace_id,
                    "FORM_FIELD_CREATED",
                    "form_field",
                    field.id,
                    None,
                    self._field_state(field),
                )
            )
            await self.repository.flush()
        return field

    async def _validate_entity_type(self, workspace_id: UUID, entity_type_id: object) -> None:
        if entity_type_id is None:
            return
        if (
            not isinstance(entity_type_id, UUID)
            or await self.repository.entity_type_in_workspace(entity_type_id, workspace_id) is None
        ):
            raise InvalidMetadataError({"field": "entity_type_id", "reason": "not_found"})

    @staticmethod
    def _section_keys(form: FormDefinition) -> set[object]:
        sections = form.schema_json.get("sections", [])
        if not isinstance(sections, (list, tuple)):
            return set()
        return {
            section.get("key")
            for section in sections
            if isinstance(section, dict) and isinstance(section.get("key"), str)
        }

    @staticmethod
    def _rule_mapping(value: object) -> dict[str, object]:
        if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
            raise InvalidFormRuleError("Rule must be an object with string keys.")
        return value

    @staticmethod
    def _form_state(form: FormDefinition) -> dict[str, object]:
        return {
            "key": form.key,
            "name": form.name,
            "entity_type_id": str(form.entity_type_id) if form.entity_type_id else None,
            "description": form.description,
            "version_number": form.version_number,
            "lifecycle_status": form.lifecycle_status,
            "schema_json": form.schema_json,
        }

    @staticmethod
    def _field_state(field: FormField) -> dict[str, object]:
        return {
            "form_definition_id": str(field.form_definition_id),
            "attribute_definition_id": (
                str(field.attribute_definition_id) if field.attribute_definition_id else None
            ),
            "key": field.key,
            "label": field.label,
            "field_type": field.field_type,
            "section_key": field.section_key,
            "display_order": field.display_order,
            "is_required": field.is_required,
            "is_read_only": field.is_read_only,
            "configuration": field.configuration,
            "visibility_rule": field.visibility_rule,
            "validation_rule": field.validation_rule,
            "inheritance_rule": field.inheritance_rule,
        }

    def _audit_log(
        self,
        audit: AuditContext,
        workspace_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        before_state: dict[str, object] | None,
        after_state: dict[str, object] | None,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )
