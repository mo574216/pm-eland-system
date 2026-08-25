"""Entity-type and attribute-definition lifecycle policies."""

import re
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    StaleVersionError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.metadata import AttributeDefinition, EntityType
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.metadata_validation import MetadataValueValidator


class MetadataService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = MetadataRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

    async def _require_workspace_access(self, workspace_id: UUID) -> None:
        workspace = await self.workspace_repository.accessible_workspace(
            workspace_id, self.actor.user.id
        )
        if workspace is None:
            raise WorkspaceAccessDeniedError

    async def _require_manage(self, workspace_id: UUID) -> None:
        await self._require_workspace_access(workspace_id)
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if PermissionCode.METADATA_MANAGE.value not in effective:
            raise PermissionDeniedError

    def _audit_log(
        self,
        entity_type: EntityType,
        action: str,
        before_state: dict[str, object] | None,
        after_state: dict[str, object] | None,
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=entity_type.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="entity_type",
            resource_id=entity_type.id,
            before_state=before_state,
            after_state=after_state,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    @staticmethod
    def _state(entity_type: EntityType) -> dict[str, object]:
        return {
            "key": entity_type.key,
            "name": entity_type.name,
            "plural_name": entity_type.plural_name,
            "description": entity_type.description,
            "is_active": entity_type.is_active,
            "configuration": entity_type.configuration,
            "version": entity_type.version,
        }

    async def create_entity_type(
        self,
        workspace_id: UUID,
        *,
        values: dict[str, object],
        audit: AuditContext,
    ) -> EntityType:
        async with self.session.begin():
            await self._require_manage(workspace_id)
            key = (
                str(values["key"])
                if values.get("key") is not None
                else self._generated_key("type")
            )
            values["key"] = key
            if await self.repository.entity_type_by_key(workspace_id, key) is not None:
                raise ResourceConflictError
            entity_type = EntityType(
                id=uuid4(),
                workspace_id=workspace_id,
                created_by=self.actor.user.id,
                is_active=True,
                version=1,
                **values,
            )
            self.repository.add_entity_type(entity_type)
            self.repository.add_audit_log(
                self._audit_log(
                    entity_type,
                    "ENTITY_TYPE_CREATED",
                    None,
                    self._state(entity_type),
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return entity_type

    async def list_entity_types(
        self,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
        active: bool | None,
        search: str | None,
    ) -> tuple[tuple[EntityType, ...], int]:
        await self._require_workspace_access(workspace_id)
        return await self.repository.list_entity_types(
            workspace_id,
            self.actor.user.id,
            page=page,
            page_size=page_size,
            active=active,
            search=search,
        )

    async def get_entity_type(self, entity_type_id: UUID) -> EntityType:
        entity_type = await self.repository.accessible_entity_type(
            entity_type_id, self.actor.user.id
        )
        if entity_type is None:
            raise ResourceNotFoundError
        return entity_type

    async def update_entity_type(
        self,
        entity_type_id: UUID,
        *,
        expected_version: int,
        values: dict[str, object],
        audit: AuditContext,
    ) -> EntityType:
        async with self.session.begin():
            entity_type = await self.get_entity_type(entity_type_id)
            await self._require_manage(entity_type.workspace_id)
            before_state = self._state(entity_type)
            updated = await self.repository.update_entity_type(
                entity_type_id, expected_version, values
            )
            if updated is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._audit_log(
                    updated,
                    "ENTITY_TYPE_UPDATED",
                    before_state,
                    self._state(updated),
                    audit,
                )
            )
        return updated

    async def archive_entity_type(
        self, entity_type_id: UUID, *, expected_version: int, audit: AuditContext
    ) -> None:
        async with self.session.begin():
            entity_type = await self.get_entity_type(entity_type_id)
            await self._require_manage(entity_type.workspace_id)
            before_state = self._state(entity_type)
            archived = await self.repository.archive_entity_type(entity_type_id, expected_version)
            if archived is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._audit_log(
                    archived,
                    "ENTITY_TYPE_ARCHIVED",
                    before_state,
                    self._state(archived),
                    audit,
                )
            )

    @staticmethod
    def _attribute_state(attribute: AttributeDefinition) -> dict[str, object]:
        return {
            "key": attribute.key,
            "label": attribute.label,
            "data_type": attribute.data_type,
            "is_required": attribute.is_required,
            "is_read_only": attribute.is_read_only,
            "default_value": attribute.default_value,
            "validation_config": attribute.validation_config,
            "display_config": attribute.display_config,
            "inheritance_config": attribute.inheritance_config,
            "display_order": attribute.display_order,
            "is_active": attribute.is_active,
            "version": attribute.version,
        }

    def _attribute_audit_log(
        self,
        attribute: AttributeDefinition,
        workspace_id: UUID,
        action: str,
        before_state: dict[str, object] | None,
        after_state: dict[str, object] | None,
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="attribute_definition",
            resource_id=attribute.id,
            before_state=before_state,
            after_state=after_state,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    @staticmethod
    def _validate_config_keys(value: object, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str) or re.fullmatch(r"[a-z][a-z0-9_]*", key) is None:
                    raise InvalidMetadataError({"field": path, "reason": "invalid_key"})
                MetadataService._validate_config_keys(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                MetadataService._validate_config_keys(child, f"{path}[{index}]")

    async def _validate_attribute_configuration(
        self,
        *,
        entity_type: EntityType,
        data_type: str,
        validation_config: dict[str, object],
        display_config: dict[str, object],
        inheritance_config: dict[str, object],
    ) -> None:
        self._validate_config_keys(validation_config, "validation_config")
        self._validate_config_keys(display_config, "display_config")
        self._validate_config_keys(inheritance_config, "inheritance_config")

        for key in ("min_length", "max_length"):
            constraint = validation_config.get(key)
            if constraint is not None and (
                not isinstance(constraint, int) or isinstance(constraint, bool) or constraint < 0
            ):
                raise InvalidMetadataError(
                    {"field": f"validation_config.{key}", "reason": "invalid_value"}
                )
        min_length = validation_config.get("min_length")
        max_length = validation_config.get("max_length")
        if isinstance(min_length, int) and isinstance(max_length, int) and min_length > max_length:
            raise InvalidMetadataError({"field": "validation_config", "reason": "invalid_range"})
        for key in ("minimum", "maximum"):
            constraint = validation_config.get(key)
            if constraint is not None and (
                not isinstance(constraint, (int, float)) or isinstance(constraint, bool)
            ):
                raise InvalidMetadataError(
                    {"field": f"validation_config.{key}", "reason": "invalid_value"}
                )
        minimum = validation_config.get("minimum")
        maximum = validation_config.get("maximum")
        if (
            isinstance(minimum, (int, float))
            and not isinstance(minimum, bool)
            and isinstance(maximum, (int, float))
            and not isinstance(maximum, bool)
            and minimum > maximum
        ):
            raise InvalidMetadataError({"field": "validation_config", "reason": "invalid_range"})
        pattern = validation_config.get("pattern")
        if pattern is not None and (
            not isinstance(pattern, str) or not MetadataValueValidator.is_safe_pattern(pattern)
        ):
            raise InvalidMetadataError(
                {"field": "validation_config.pattern", "reason": "unsafe_pattern"}
            )

        options = display_config.get("options")
        if data_type in {"ENUM", "MULTI_ENUM"}:
            if not isinstance(options, list) or not options:
                raise InvalidMetadataError(
                    {"field": "display_config.options", "reason": "required"}
                )
            values: set[str] = set()
            for option in options:
                if not isinstance(option, dict):
                    raise InvalidMetadataError(
                        {"field": "display_config.options", "reason": "invalid_option"}
                    )
                value = option.get("value")
                label = option.get("label")
                if (
                    not isinstance(value, str)
                    or not value
                    or not isinstance(label, str)
                    or not label
                ):
                    raise InvalidMetadataError(
                        {"field": "display_config.options", "reason": "invalid_option"}
                    )
                if value in values:
                    raise InvalidMetadataError(
                        {"field": "display_config.options", "reason": "duplicate_value"}
                    )
                values.add(value)
        elif options is not None:
            raise InvalidMetadataError(
                {"field": "display_config.options", "reason": "unsupported_for_type"}
            )

        if not inheritance_config:
            return
        if set(inheritance_config) != {"source", "mode"}:
            raise InvalidMetadataError(
                {"field": "inheritance_config", "reason": "invalid_structure"}
            )
        if inheritance_config["mode"] not in {"prefill", "read_only"}:
            raise InvalidMetadataError(
                {"field": "inheritance_config.mode", "reason": "invalid_value"}
            )
        source = inheritance_config["source"]
        if not isinstance(source, dict):
            raise InvalidMetadataError(
                {"field": "inheritance_config.source", "reason": "invalid_structure"}
            )
        if not {"scope", "attribute"}.issubset(source) or not set(source).issubset(
            {"scope", "attribute", "entity_type_id"}
        ):
            raise InvalidMetadataError(
                {"field": "inheritance_config.source", "reason": "invalid_structure"}
            )
        scope = source["scope"]
        source_key = source["attribute"]
        if scope not in {"current", "parent", "reference"} or not isinstance(source_key, str):
            raise InvalidMetadataError(
                {"field": "inheritance_config.source", "reason": "invalid_reference"}
            )
        source_type_id = entity_type.id
        if "entity_type_id" in source:
            try:
                source_type_id = UUID(str(source["entity_type_id"]))
            except ValueError as exc:
                raise InvalidMetadataError(
                    {"field": "inheritance_config.source.entity_type_id", "reason": "invalid_uuid"}
                ) from exc
        elif scope == "reference":
            raise InvalidMetadataError(
                {"field": "inheritance_config.source.entity_type_id", "reason": "required"}
            )
        source_type = await self.repository.entity_type_in_workspace(
            source_type_id, entity_type.workspace_id
        )
        source_attribute = await self.repository.attribute_by_key(source_type_id, source_key)
        if source_type is None or source_attribute is None:
            raise InvalidMetadataError(
                {"field": "inheritance_config.source", "reason": "not_found"}
            )

    async def create_attribute(
        self,
        entity_type_id: UUID,
        *,
        values: dict[str, object],
        audit: AuditContext,
    ) -> AttributeDefinition:
        async with self.session.begin():
            entity_type = await self.get_entity_type(entity_type_id)
            await self._require_manage(entity_type.workspace_id)
            key = (
                str(values["key"])
                if values.get("key") is not None
                else self._generated_key("attribute")
            )
            values["key"] = key
            if await self.repository.attribute_by_key(entity_type_id, key) is not None:
                raise ResourceConflictError
            await self._validate_attribute_configuration(
                entity_type=entity_type,
                data_type=str(values["data_type"]),
                validation_config=cast(dict[str, object], values["validation_config"]),
                display_config=cast(dict[str, object], values["display_config"]),
                inheritance_config=cast(dict[str, object], values["inheritance_config"]),
            )
            attribute = AttributeDefinition(
                id=uuid4(), entity_type_id=entity_type_id, is_active=True, version=1, **values
            )
            self.repository.add_attribute(attribute)
            self.repository.add_audit_log(
                self._attribute_audit_log(
                    attribute,
                    entity_type.workspace_id,
                    "ATTRIBUTE_DEFINITION_CREATED",
                    None,
                    self._attribute_state(attribute),
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return attribute

    @staticmethod
    def _generated_key(resource: str) -> str:
        """Create an opaque stable key without deriving identifiers from display text."""
        return f"{resource}_{uuid4().hex}"

    async def list_attributes(self, entity_type_id: UUID) -> tuple[AttributeDefinition, ...]:
        await self.get_entity_type(entity_type_id)
        return await self.repository.list_attributes(entity_type_id)

    async def update_attribute(
        self,
        attribute_id: UUID,
        *,
        expected_version: int,
        values: dict[str, object],
        audit: AuditContext,
    ) -> AttributeDefinition:
        async with self.session.begin():
            accessible = await self.repository.accessible_attribute(
                attribute_id, self.actor.user.id
            )
            if accessible is None:
                raise ResourceNotFoundError
            attribute, entity_type = accessible
            await self._require_manage(entity_type.workspace_id)
            await self._validate_attribute_configuration(
                entity_type=entity_type,
                data_type=attribute.data_type,
                validation_config=cast(
                    dict[str, object], values.get("validation_config", attribute.validation_config)
                ),
                display_config=cast(
                    dict[str, object], values.get("display_config", attribute.display_config)
                ),
                inheritance_config=cast(
                    dict[str, object],
                    values.get("inheritance_config", attribute.inheritance_config),
                ),
            )
            before_state = self._attribute_state(attribute)
            updated = await self.repository.update_attribute(attribute_id, expected_version, values)
            if updated is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._attribute_audit_log(
                    updated,
                    entity_type.workspace_id,
                    "ATTRIBUTE_DEFINITION_UPDATED",
                    before_state,
                    self._attribute_state(updated),
                    audit,
                )
            )
        return updated

    async def deactivate_attribute(
        self, attribute_id: UUID, *, expected_version: int, audit: AuditContext
    ) -> None:
        async with self.session.begin():
            accessible = await self.repository.accessible_attribute(
                attribute_id, self.actor.user.id
            )
            if accessible is None:
                raise ResourceNotFoundError
            attribute, entity_type = accessible
            await self._require_manage(entity_type.workspace_id)
            before_state = self._attribute_state(attribute)
            deactivated = await self.repository.deactivate_attribute(attribute_id, expected_version)
            if deactivated is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._attribute_audit_log(
                    deactivated,
                    entity_type.workspace_id,
                    "ATTRIBUTE_DEFINITION_DEACTIVATED",
                    before_state,
                    self._attribute_state(deactivated),
                    audit,
                )
            )
