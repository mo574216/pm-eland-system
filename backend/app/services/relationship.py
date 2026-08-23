"""Authorization, validation, and audit for generic relationships."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidRelationshipError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.relationship import EntityRelationship, RelationshipType
from app.repositories.relationship import RelationshipRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


class RelationshipService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.workspace_repository = WorkspaceRepository(session)
        self.repository = RelationshipRepository(session)

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

    async def create_relationship_type(
        self,
        workspace_id: UUID,
        *,
        values: dict[str, object],
        audit: AuditContext,
    ) -> RelationshipType:
        async with self.session.begin():
            await self._require_permission(workspace_id, PermissionCode.METADATA_MANAGE)
            key = str(values["key"])
            if await self.repository.relationship_type_by_key(workspace_id, key) is not None:
                raise ResourceConflictError
            for field in ("source_type_id", "target_type_id"):
                entity_type_id = values.get(field)
                if entity_type_id is not None and (
                    not isinstance(entity_type_id, UUID)
                    or await self.repository.entity_type_in_workspace(entity_type_id, workspace_id)
                    is None
                ):
                    raise InvalidRelationshipError({"field": field, "reason": "invalid_type"})
            relationship_type = RelationshipType(
                id=uuid4(), workspace_id=workspace_id, is_active=True, **values
            )
            self.repository.add_relationship_type(relationship_type)
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    workspace_id,
                    "RELATIONSHIP_TYPE_CREATED",
                    "relationship_type",
                    relationship_type.id,
                    None,
                    self._relationship_type_state(relationship_type),
                )
            )
            await self.repository.flush()
        return relationship_type

    async def list_relationship_types(
        self, workspace_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[RelationshipType, ...], int]:
        await self._require_permission(workspace_id, PermissionCode.ENTITY_READ)
        return await self.repository.list_relationship_types(
            workspace_id,
            self.actor.user.id,
            page=page,
            page_size=page_size,
        )

    async def create_relationship(
        self,
        workspace_id: UUID,
        *,
        relationship_type_id: UUID,
        source_entity_id: UUID,
        target_entity_id: UUID,
        attributes: dict[str, object],
        audit: AuditContext,
    ) -> EntityRelationship:
        async with self.session.begin():
            await self._require_permission(workspace_id, PermissionCode.RELATIONSHIP_MANAGE)
            if source_entity_id == target_entity_id:
                raise InvalidRelationshipError({"reason": "self_link"})
            relationship_type = await self.repository.relationship_type_in_workspace(
                relationship_type_id, workspace_id
            )
            if relationship_type is None or not relationship_type.is_active:
                raise ResourceNotFoundError
            source = await self.repository.entity_in_workspace(source_entity_id, workspace_id)
            target = await self.repository.entity_in_workspace(target_entity_id, workspace_id)
            if source is None or target is None:
                raise ResourceNotFoundError
            if (
                relationship_type.source_type_id is not None
                and relationship_type.source_type_id != source.entity_type_id
            ):
                raise InvalidRelationshipError(
                    {"field": "source_entity_id", "reason": "type_not_allowed"}
                )
            if (
                relationship_type.target_type_id is not None
                and relationship_type.target_type_id != target.entity_type_id
            ):
                raise InvalidRelationshipError(
                    {"field": "target_entity_id", "reason": "type_not_allowed"}
                )
            await self.repository.acquire_workspace_lock(workspace_id)
            if relationship_type.configuration.get("allow_duplicates") is False and (
                await self.repository.duplicate_exists(
                    relationship_type, source_entity_id, target_entity_id
                )
            ):
                raise InvalidRelationshipError({"reason": "duplicate"})
            relationship = EntityRelationship(
                id=uuid4(),
                workspace_id=workspace_id,
                relationship_type_id=relationship_type_id,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                attributes=attributes,
                created_by=self.actor.user.id,
            )
            self.repository.add_relationship(relationship)
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    workspace_id,
                    "RELATIONSHIP_CREATED",
                    "entity_relationship",
                    relationship.id,
                    None,
                    self._relationship_state(relationship),
                )
            )
            await self.repository.flush()
        return relationship

    async def list_relationships(
        self,
        entity_id: UUID,
        *,
        direction: str,
        relationship_type_id: UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[tuple[EntityRelationship, ...], int]:
        entity = await self.repository.accessible_entity(entity_id, self.actor.user.id)
        if entity is None:
            raise ResourceNotFoundError
        await self._require_permission(entity.workspace_id, PermissionCode.ENTITY_READ)
        if relationship_type_id is not None:
            relationship_type = await self.repository.relationship_type_in_workspace(
                relationship_type_id, entity.workspace_id
            )
            if relationship_type is None:
                raise ResourceNotFoundError
        return await self.repository.list_relationships(
            entity_id,
            entity.workspace_id,
            direction=direction,
            relationship_type_id=relationship_type_id,
            page=page,
            page_size=page_size,
        )

    async def delete_relationship(self, relationship_id: UUID, *, audit: AuditContext) -> None:
        async with self.session.begin():
            relationship = await self.repository.accessible_relationship(
                relationship_id, self.actor.user.id
            )
            if relationship is None:
                raise ResourceNotFoundError
            await self._require_permission(
                relationship.workspace_id, PermissionCode.RELATIONSHIP_MANAGE
            )
            before_state = self._relationship_state(relationship)
            deleted = await self.repository.soft_delete_relationship(relationship_id)
            if deleted is None:
                raise ResourceNotFoundError
            self.repository.add_audit_log(
                self._audit_log(
                    audit,
                    deleted.workspace_id,
                    "RELATIONSHIP_DELETED",
                    "entity_relationship",
                    deleted.id,
                    before_state,
                    None,
                )
            )

    @staticmethod
    def _relationship_type_state(value: RelationshipType) -> dict[str, object]:
        return {
            "key": value.key,
            "name": value.name,
            "directionality": value.directionality,
            "source_type_id": str(value.source_type_id) if value.source_type_id else None,
            "target_type_id": str(value.target_type_id) if value.target_type_id else None,
            "configuration": value.configuration,
            "is_active": value.is_active,
        }

    @staticmethod
    def _relationship_state(value: EntityRelationship) -> dict[str, object]:
        return {
            "relationship_type_id": str(value.relationship_type_id),
            "source_entity_id": str(value.source_entity_id),
            "target_entity_id": str(value.target_entity_id),
            "attributes": value.attributes,
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
