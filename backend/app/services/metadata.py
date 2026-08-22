"""Entity-type lifecycle policies for generic metadata."""

from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    StaleVersionError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.metadata import EntityType
from app.repositories.metadata import MetadataRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


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
            key = str(values["key"])
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
