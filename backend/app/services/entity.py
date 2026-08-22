"""Transactional generic entity creation service."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceNotFoundError,
    StaleVersionError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.core.persian_text import normalize_persian_search_text
from app.models.entity import EntityObject
from app.models.identity import AuditLog
from app.repositories.entity import EntityRecord, EntityRepository, EntityTreeRecord
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.metadata_validation import (
    MetadataValueValidator,
    ReferenceResolver,
    ValidationMode,
)


class EntityReferenceResolver(ReferenceResolver):
    def __init__(self, repository: EntityRepository) -> None:
        self.repository = repository

    async def exists(self, kind: str, reference_id: UUID, workspace_id: UUID) -> bool:
        if kind == "USER_REFERENCE":
            return await self.repository.user_reference_exists(reference_id, workspace_id)
        if kind == "ENTITY_REFERENCE":
            return await self.repository.entity_in_workspace(reference_id, workspace_id) is not None
        # Document/file persistence is introduced by DOC-DB-001. Reject unresolved
        # file references safely until that workspace-scoped repository exists.
        return False


class EntityService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.workspace_repository = WorkspaceRepository(session)
        self.metadata_repository = MetadataRepository(session)
        self.repository = EntityRepository(session)
        self.validator = MetadataValueValidator(EntityReferenceResolver(self.repository))

    async def _require_create(self, workspace_id: UUID) -> None:
        await self._require_permission(workspace_id, PermissionCode.ENTITY_CREATE)

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

    async def create_entity(
        self,
        workspace_id: UUID,
        *,
        entity_type_id: UUID,
        parent_id: UUID | None,
        name: str,
        description: str | None,
        attributes: dict[str, object],
        audit: AuditContext,
    ) -> EntityRecord:
        async with self.session.begin():
            await self._require_create(workspace_id)
            entity_type = await self.metadata_repository.entity_type_in_workspace(
                entity_type_id, workspace_id
            )
            if entity_type is None or not entity_type.is_active:
                raise ResourceNotFoundError
            if parent_id is not None:
                parent = await self.repository.entity_in_workspace(parent_id, workspace_id)
                if parent is None or parent.status != "ACTIVE":
                    raise ResourceNotFoundError
            definitions = await self.metadata_repository.list_attributes(entity_type_id)
            validation = await self.validator.validate_attributes(
                entity_type, definitions, attributes, ValidationMode.CREATE
            )
            if not validation.is_valid:
                raise InvalidMetadataError(
                    {
                        "fields": [
                            {"field": error.field, "code": error.code}
                            for error in validation.errors
                        ]
                    }
                )
            entity = EntityObject(
                id=uuid4(),
                workspace_id=workspace_id,
                entity_type_id=entity_type_id,
                parent_id=parent_id,
                name=name,
                description=description,
                status="ACTIVE",
                attributes=validation.values,
                created_by=self.actor.user.id,
                updated_by=self.actor.user.id,
                version=1,
            )
            self.repository.add_entity(entity)
            self.repository.add_audit_log(
                AuditLog(
                    id=uuid4(),
                    request_id=audit.request_id,
                    workspace_id=workspace_id,
                    user_id=self.actor.user.id,
                    action="ENTITY_CREATED",
                    resource_type="entity_object",
                    resource_id=entity.id,
                    before_state=None,
                    after_state={
                        "entity_type_id": str(entity_type_id),
                        "parent_id": str(parent_id) if parent_id else None,
                        "name": name,
                        "status": "ACTIVE",
                        "attributes": validation.values,
                        "version": 1,
                    },
                    client_ip=audit.client_ip,
                    user_agent=audit.user_agent,
                )
            )
            await self.repository.flush()
        return EntityRecord(entity, entity_type)

    async def get_entity(self, entity_id: UUID) -> EntityRecord:
        record = await self.repository.accessible_entity_record(entity_id, self.actor.user.id)
        if record is None:
            raise ResourceNotFoundError
        await self._require_permission(record.entity.workspace_id, PermissionCode.ENTITY_READ)
        return record

    async def list_entities(
        self,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
        status: str | None,
        entity_type_id: UUID | None,
        parent_id: UUID | None,
        search: str | None,
    ) -> tuple[tuple[EntityRecord, ...], int]:
        await self._require_permission(workspace_id, PermissionCode.ENTITY_READ)
        return await self.repository.list_entities(
            workspace_id,
            self.actor.user.id,
            page=page,
            page_size=page_size,
            status=status,
            entity_type_id=entity_type_id,
            parent_id=parent_id,
            search=normalize_persian_search_text(search) if search else None,
        )

    async def get_entity_tree(
        self,
        workspace_id: UUID,
        *,
        root_id: UUID | None,
        max_depth: int | None,
        include_type: bool,
    ) -> tuple[EntityTreeRecord, ...]:
        await self._require_permission(workspace_id, PermissionCode.ENTITY_READ)
        records = await self.repository.entity_tree(
            workspace_id,
            self.actor.user.id,
            root_id=root_id,
            max_depth=max_depth,
            include_type=include_type,
        )
        if root_id is not None and not records:
            raise ResourceNotFoundError
        return records

    @staticmethod
    def _entity_state(entity: EntityObject) -> dict[str, object]:
        return {
            "entity_type_id": str(entity.entity_type_id),
            "parent_id": str(entity.parent_id) if entity.parent_id else None,
            "name": entity.name,
            "description": entity.description,
            "status": entity.status,
            "attributes": entity.attributes,
            "version": entity.version,
        }

    def _mutation_audit(
        self,
        entity: EntityObject,
        action: str,
        before_state: dict[str, object],
        after_state: dict[str, object],
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=entity.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="entity_object",
            resource_id=entity.id,
            before_state=before_state,
            after_state=after_state,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    async def update_entity(
        self,
        entity_id: UUID,
        *,
        expected_version: int,
        values: dict[str, object],
        audit: AuditContext,
    ) -> EntityRecord:
        async with self.session.begin():
            record = await self.repository.accessible_entity_record(entity_id, self.actor.user.id)
            if record is None or record.entity.status != "ACTIVE":
                raise ResourceNotFoundError
            entity = record.entity
            await self._require_permission(entity.workspace_id, PermissionCode.ENTITY_UPDATE)
            before_state = self._entity_state(entity)
            update_values = dict(values)
            changed_attributes = update_values.get("attributes")
            if changed_attributes is not None:
                if not isinstance(changed_attributes, dict):
                    raise InvalidMetadataError
                definitions = await self.metadata_repository.list_attributes(entity.entity_type_id)
                validation = await self.validator.validate_attributes(
                    record.entity_type,
                    definitions,
                    changed_attributes,
                    ValidationMode.UPDATE,
                )
                if not validation.is_valid:
                    raise InvalidMetadataError(
                        {
                            "fields": [
                                {"field": error.field, "code": error.code}
                                for error in validation.errors
                            ]
                        }
                    )
                update_values["attributes"] = {
                    **entity.attributes,
                    **validation.values,
                }
            update_values["updated_by"] = self.actor.user.id
            updated = await self.repository.update_entity(
                entity_id, expected_version, update_values
            )
            if updated is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._mutation_audit(
                    updated,
                    "ENTITY_UPDATED",
                    before_state,
                    self._entity_state(updated),
                    audit,
                )
            )
        return EntityRecord(updated, record.entity_type)

    async def archive_entity(
        self, entity_id: UUID, *, expected_version: int, audit: AuditContext
    ) -> None:
        async with self.session.begin():
            record = await self.repository.accessible_entity_record(entity_id, self.actor.user.id)
            if record is None or record.entity.status != "ACTIVE":
                raise ResourceNotFoundError
            await self._require_permission(
                record.entity.workspace_id, PermissionCode.ENTITY_ARCHIVE
            )
            before_state = self._entity_state(record.entity)
            archived = await self.repository.archive_entity(
                entity_id, expected_version, self.actor.user.id
            )
            if archived is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._mutation_audit(
                    archived,
                    "ENTITY_ARCHIVED",
                    before_state,
                    self._entity_state(archived),
                    audit,
                )
            )
