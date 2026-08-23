"""Draft form definition authorization, validation, and audit service."""

from copy import deepcopy
from typing import cast
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
from app.models.entity import EntityObject
from app.models.form import FormDefinition, FormField
from app.models.identity import AuditLog
from app.models.metadata import AttributeDefinition
from app.repositories.entity import EntityRepository
from app.repositories.form import FormRecord, FormRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.form import (
    FormFieldType,
    FormRenderField,
    FormRenderResponse,
    FormRenderSection,
    FormRenderSummary,
    FormRenderValueSource,
    FormSchemaDefinition,
)
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
        self.entity_repository = EntityRepository(session)
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

    async def render_form(
        self,
        form_id: UUID,
        *,
        entity_id: UUID | None,
        draft_values: dict[str, object] | None = None,
    ) -> FormRenderResponse:
        record = await self.repository.accessible_form_record(form_id, self.actor.user.id)
        if record is None:
            raise ResourceNotFoundError
        form = record.form
        permission = (
            PermissionCode.FORM_DESIGN
            if form.lifecycle_status == "DRAFT"
            else PermissionCode.ENTITY_READ
        )
        await self._require_permission(form.workspace_id, permission)

        entity: EntityObject | None = None
        if entity_id is not None:
            entity = await self.entity_repository.entity_in_workspace(entity_id, form.workspace_id)
            if entity is None or entity.status == "DELETED":
                raise ResourceNotFoundError
            if form.entity_type_id is not None and entity.entity_type_id != form.entity_type_id:
                raise InvalidMetadataError({"field": "entity_id", "reason": "wrong_entity_type"})

        attribute_ids = frozenset(
            field.attribute_definition_id
            for field in record.fields
            if field.attribute_definition_id is not None
        )
        attributes = await self.repository.attributes_in_workspace(attribute_ids, form.workspace_id)
        if len(attributes) != len(attribute_ids):
            raise InvalidMetadataError({"field": "fields", "reason": "attribute_not_found"})
        context = await self._render_context(
            form.workspace_id, entity, record.fields, attributes, draft_values
        )
        sections = self._render_sections(form, record.fields, attributes, context)
        return FormRenderResponse(
            form=FormRenderSummary(
                id=form.id,
                key=form.key,
                name=form.name,
                version_number=form.version_number,
                lifecycle_status=form.lifecycle_status,
            ),
            entity_id=entity_id,
            sections=sections,
        )

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

    async def publish_form(self, form_id: UUID, *, audit: AuditContext) -> FormRecord:
        async with self.session.begin():
            form = await self.repository.lock_accessible_form(form_id, self.actor.user.id)
            if form is None:
                raise ResourceNotFoundError
            await self._require_permission(form.workspace_id, PermissionCode.FORM_DESIGN)
            if form.lifecycle_status != "DRAFT":
                raise ResourceConflictError
            fields = await self.repository.list_fields(form.id)
            await self._validate_publishable(form, fields)
            before_state = self._form_state(form)
            published = await self.repository.publish_draft(form.id)
            if published is None:
                raise ResourceConflictError
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    published.workspace_id,
                    "FORM_PUBLISHED",
                    "form_definition",
                    published.id,
                    before_state,
                    self._form_state(published),
                )
            )
        return FormRecord(published, fields)

    async def create_new_version(self, form_id: UUID, *, audit: AuditContext) -> FormRecord:
        async with self.session.begin():
            source = await self.repository.lock_accessible_form(form_id, self.actor.user.id)
            if source is None:
                raise ResourceNotFoundError
            await self._require_permission(source.workspace_id, PermissionCode.FORM_DESIGN)
            if source.lifecycle_status != "PUBLISHED":
                raise ResourceConflictError
            source_fields = await self.repository.list_fields(source.id)
            await self.repository.acquire_workspace_lock(source.workspace_id)
            next_version = await self.repository.next_version_number(
                source.workspace_id, source.key
            )
            draft = FormDefinition(
                id=uuid4(),
                workspace_id=source.workspace_id,
                entity_type_id=source.entity_type_id,
                key=source.key,
                name=source.name,
                description=source.description,
                version_number=next_version,
                lifecycle_status="DRAFT",
                schema_json=deepcopy(source.schema_json),
                created_by=self.actor.user.id,
            )
            self.repository.add_form(draft)
            copied_fields = tuple(
                FormField(
                    id=uuid4(),
                    form_definition_id=draft.id,
                    attribute_definition_id=field.attribute_definition_id,
                    key=field.key,
                    label=field.label,
                    field_type=field.field_type,
                    section_key=field.section_key,
                    display_order=field.display_order,
                    is_required=field.is_required,
                    is_read_only=field.is_read_only,
                    configuration=deepcopy(field.configuration),
                    visibility_rule=deepcopy(field.visibility_rule),
                    validation_rule=deepcopy(field.validation_rule),
                    inheritance_rule=deepcopy(field.inheritance_rule),
                )
                for field in source_fields
            )
            for field in copied_fields:
                self.repository.add_field(field)
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    draft.workspace_id,
                    "FORM_VERSION_CREATED",
                    "form_definition",
                    draft.id,
                    {"source_form_id": str(source.id), **self._form_state(source)},
                    self._form_state(draft),
                )
            )
            await self.repository.flush()
        return FormRecord(draft, copied_fields)

    async def _render_context(
        self,
        workspace_id: UUID,
        entity: EntityObject | None,
        fields: tuple[FormField, ...],
        attributes: dict[UUID, AttributeDefinition],
        draft_values: dict[str, object] | None,
    ) -> dict[str, object]:
        current = self._entity_state(entity)
        parent: dict[str, object] = {}
        if entity is not None and entity.parent_id is not None:
            parent_entity = await self.entity_repository.entity_in_workspace(
                entity.parent_id, workspace_id
            )
            if parent_entity is not None and parent_entity.status != "DELETED":
                parent = self._entity_state(parent_entity)

        for field in fields:
            attribute = (
                attributes.get(field.attribute_definition_id)
                if field.attribute_definition_id is not None
                else None
            )
            if attribute is None or attribute.key == field.key:
                continue
            if attribute.key in current:
                current[field.key] = current[attribute.key]
            if attribute.key in parent:
                parent[field.key] = parent[attribute.key]
        if draft_values is not None:
            current.update(draft_values)
            for field in fields:
                if field.key not in draft_values or field.attribute_definition_id is None:
                    continue
                attribute = attributes.get(field.attribute_definition_id)
                if attribute is not None:
                    current[attribute.key] = draft_values[field.key]

        referenced_ids: set[UUID] = set()
        reference_keys: dict[UUID, set[str]] = {}
        if entity is not None:
            for field in fields:
                attribute = (
                    attributes.get(field.attribute_definition_id)
                    if field.attribute_definition_id is not None
                    else None
                )
                if attribute is None or attribute.data_type != "ENTITY_REFERENCE":
                    continue
                reference_id = self._uuid_value(entity.attributes.get(attribute.key))
                if reference_id is None:
                    continue
                referenced_ids.add(reference_id)
                reference_keys.setdefault(reference_id, set()).update({attribute.key, field.key})
        referenced_entities = await self.entity_repository.entities_in_workspace(
            frozenset(referenced_ids), workspace_id
        )
        referenced: dict[str, object] = {}
        for reference_id, keys in reference_keys.items():
            reference = referenced_entities.get(reference_id)
            if reference is None:
                continue
            state = self._entity_state(reference)
            for key in keys:
                referenced[key] = state

        return {
            "current": current,
            "parent": parent,
            "referenced": referenced,
            "user": {
                "id": str(self.actor.user.id),
                "username": self.actor.user.username,
                "display_name": self.actor.user.display_name,
                "roles": list(self.actor.roles),
            },
        }

    def _render_sections(
        self,
        form: FormDefinition,
        fields: tuple[FormField, ...],
        attributes: dict[UUID, AttributeDefinition],
        context: dict[str, object],
    ) -> tuple[FormRenderSection, ...]:
        try:
            schema = FormSchemaDefinition.model_validate(form.schema_json)
        except ValueError as error:
            raise InvalidMetadataError(
                {"field": "schema_json", "reason": "invalid_schema"}
            ) from error
        configured_keys = {section.key for section in schema.sections}
        grouped: dict[str | None, list[FormRenderField]] = {
            section.key: [] for section in schema.sections
        }
        grouped[None] = []
        for field in fields:
            if field.section_key is not None and field.section_key not in configured_keys:
                raise InvalidMetadataError({"field": field.key, "reason": "invalid_section"})
            grouped[field.section_key].append(self._render_field(field, attributes, context))

        result = [
            FormRenderSection(
                key=section.key,
                label=section.label,
                order=section.display_order,
                configuration=section.configuration,
                fields=tuple(grouped[section.key]),
            )
            for section in sorted(
                schema.sections, key=lambda value: (value.display_order, value.key)
            )
        ]
        if grouped[None]:
            result.append(
                FormRenderSection(
                    key=None,
                    label=None,
                    order=max((section.order for section in result), default=0) + 1,
                    configuration={},
                    fields=tuple(grouped[None]),
                )
            )
        return tuple(result)

    def _render_field(
        self,
        field: FormField,
        attributes: dict[UUID, AttributeDefinition],
        context: dict[str, object],
    ) -> FormRenderField:
        try:
            evaluation = self.rule_evaluator.evaluate_field(
                is_required=field.is_required,
                is_read_only=field.is_read_only,
                visibility_rule=field.visibility_rule,
                validation_rule=field.validation_rule,
                inheritance_rule=field.inheritance_rule,
                context=context,
            )
        except InvalidFormRuleError as error:
            raise InvalidMetadataError({"field": field.key, "reason": "invalid_rule"}) from error
        attribute = (
            attributes.get(field.attribute_definition_id)
            if field.attribute_definition_id is not None
            else None
        )
        lookup_key = attribute.key if attribute is not None else field.key
        current = cast(dict[str, object], context["current"])
        value: object | None = None
        has_value = False
        value_source: FormRenderValueSource = "NONE"
        if lookup_key in current:
            value = current[lookup_key]
            has_value = True
            value_source = "CURRENT"
        elif evaluation.has_inherited_value:
            value = evaluation.inherited_value
            has_value = True
            value_source = "INHERITED"
        elif attribute is not None and attribute.default_value is not None:
            value = attribute.default_value
            has_value = True
            value_source = "DEFAULT"
        elif "default_value" in field.configuration:
            value = field.configuration["default_value"]
            has_value = True
            value_source = "DEFAULT"
        return FormRenderField(
            key=field.key,
            label=field.label,
            type=cast(FormFieldType, field.field_type),
            required=evaluation.required,
            read_only=evaluation.read_only,
            visible=evaluation.visible,
            value=value,
            has_value=has_value,
            value_source=value_source,
            configuration=field.configuration,
            visibility_rule=field.visibility_rule,
            validation_rule=field.validation_rule,
        )

    @staticmethod
    def _entity_state(entity: EntityObject | None) -> dict[str, object]:
        if entity is None:
            return {}
        return {
            **entity.attributes,
            "id": str(entity.id),
            "name": entity.name,
            "description": entity.description,
            "status": entity.status,
            "entity_type_id": str(entity.entity_type_id),
        }

    @staticmethod
    def _uuid_value(value: object) -> UUID | None:
        if isinstance(value, UUID):
            return value
        if not isinstance(value, str):
            return None
        try:
            return UUID(value)
        except ValueError:
            return None

    async def _validate_publishable(
        self, form: FormDefinition, fields: tuple[FormField, ...]
    ) -> None:
        try:
            schema = FormSchemaDefinition.model_validate(form.schema_json)
        except ValueError as error:
            raise InvalidMetadataError(
                {"field": "schema_json", "reason": "invalid_schema"}
            ) from error
        if not fields:
            raise InvalidMetadataError({"field": "fields", "reason": "required"})
        section_keys = {section.key for section in schema.sections}
        for field in fields:
            if field.section_key is not None and field.section_key not in section_keys:
                raise InvalidMetadataError({"field": field.key, "reason": "invalid_section"})
            try:
                self.rule_evaluator.validate_rules(
                    visibility_rule=field.visibility_rule,
                    validation_rule=field.validation_rule,
                    inheritance_rule=field.inheritance_rule,
                )
            except InvalidFormRuleError as error:
                raise InvalidMetadataError(
                    {"field": field.key, "reason": "invalid_rule"}
                ) from error
            if field.attribute_definition_id is not None:
                record = await self.repository.attribute_in_workspace(
                    field.attribute_definition_id, form.workspace_id
                )
                if record is None:
                    raise InvalidMetadataError({"field": field.key, "reason": "invalid_attribute"})
                attribute, entity_type = record
                if form.entity_type_id is not None and entity_type.id != form.entity_type_id:
                    raise InvalidMetadataError({"field": field.key, "reason": "wrong_entity_type"})
                if attribute.data_type != field.field_type:
                    raise InvalidMetadataError(
                        {"field": field.key, "reason": "attribute_type_mismatch"}
                    )

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
