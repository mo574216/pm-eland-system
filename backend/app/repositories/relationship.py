"""Workspace-isolated relationship persistence operations."""

from typing import cast
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import EntityObject
from app.models.identity import AuditLog
from app.models.metadata import EntityType
from app.models.relationship import EntityRelationship, RelationshipType
from app.models.workspace import WorkspaceMembership


class RelationshipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_relationship_type(self, value: RelationshipType) -> None:
        self.session.add(value)

    def add_relationship(self, value: EntityRelationship) -> None:
        self.session.add(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def acquire_workspace_lock(self, workspace_id: UUID) -> None:
        lock_key = int.from_bytes(workspace_id.bytes[:8], byteorder="big", signed=True)
        await self.session.execute(select(func.pg_advisory_xact_lock(lock_key)))

    async def relationship_type_by_key(
        self, workspace_id: UUID, key: str
    ) -> RelationshipType | None:
        statement = select(RelationshipType).where(
            RelationshipType.workspace_id == workspace_id,
            RelationshipType.key == key,
        )
        return cast(RelationshipType | None, await self.session.scalar(statement))

    async def relationship_type_in_workspace(
        self, relationship_type_id: UUID, workspace_id: UUID
    ) -> RelationshipType | None:
        statement = select(RelationshipType).where(
            RelationshipType.id == relationship_type_id,
            RelationshipType.workspace_id == workspace_id,
        )
        return cast(RelationshipType | None, await self.session.scalar(statement))

    async def entity_type_in_workspace(
        self, entity_type_id: UUID, workspace_id: UUID
    ) -> EntityType | None:
        statement = select(EntityType).where(
            EntityType.id == entity_type_id,
            EntityType.workspace_id == workspace_id,
            EntityType.deleted_at.is_(None),
            EntityType.is_active.is_(True),
        )
        return cast(EntityType | None, await self.session.scalar(statement))

    async def entity_in_workspace(self, entity_id: UUID, workspace_id: UUID) -> EntityObject | None:
        statement = select(EntityObject).where(
            EntityObject.id == entity_id,
            EntityObject.workspace_id == workspace_id,
            EntityObject.deleted_at.is_(None),
            EntityObject.status == "ACTIVE",
        )
        return cast(EntityObject | None, await self.session.scalar(statement))

    async def accessible_entity(self, entity_id: UUID, user_id: UUID) -> EntityObject | None:
        statement = (
            select(EntityObject)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityObject.workspace_id,
            )
            .where(
                EntityObject.id == entity_id,
                EntityObject.deleted_at.is_(None),
                EntityObject.status == "ACTIVE",
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(EntityObject | None, await self.session.scalar(statement))

    async def list_relationship_types(
        self,
        workspace_id: UUID,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[tuple[RelationshipType, ...], int]:
        filters = (
            RelationshipType.workspace_id == workspace_id,
            RelationshipType.is_active.is_(True),
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        )
        join = WorkspaceMembership.workspace_id == RelationshipType.workspace_id
        statement = select(RelationshipType).join(WorkspaceMembership, join)
        count_statement = select(func.count(RelationshipType.id)).join(WorkspaceMembership, join)
        items = tuple(
            (
                await self.session.scalars(
                    statement.where(*filters)
                    .order_by(RelationshipType.name, RelationshipType.id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int((await self.session.scalar(count_statement.where(*filters))) or 0)
        return items, total

    async def duplicate_exists(
        self,
        relationship_type: RelationshipType,
        source_entity_id: UUID,
        target_entity_id: UUID,
    ) -> bool:
        same_order = and_(
            EntityRelationship.source_entity_id == source_entity_id,
            EntityRelationship.target_entity_id == target_entity_id,
        )
        endpoints = same_order
        if relationship_type.directionality == "UNDIRECTED":
            endpoints = or_(
                same_order,
                and_(
                    EntityRelationship.source_entity_id == target_entity_id,
                    EntityRelationship.target_entity_id == source_entity_id,
                ),
            )
        statement = select(EntityRelationship.id).where(
            EntityRelationship.workspace_id == relationship_type.workspace_id,
            EntityRelationship.relationship_type_id == relationship_type.id,
            EntityRelationship.deleted_at.is_(None),
            endpoints,
        )
        return await self.session.scalar(statement) is not None

    async def accessible_relationship(
        self, relationship_id: UUID, user_id: UUID
    ) -> EntityRelationship | None:
        statement = (
            select(EntityRelationship)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityRelationship.workspace_id,
            )
            .where(
                EntityRelationship.id == relationship_id,
                EntityRelationship.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(EntityRelationship | None, await self.session.scalar(statement))

    async def list_relationships(
        self,
        entity_id: UUID,
        workspace_id: UUID,
        *,
        direction: str,
        relationship_type_id: UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[tuple[EntityRelationship, ...], int]:
        filters = [
            EntityRelationship.workspace_id == workspace_id,
            EntityRelationship.deleted_at.is_(None),
        ]
        if direction == "incoming":
            filters.append(EntityRelationship.target_entity_id == entity_id)
        elif direction == "outgoing":
            filters.append(EntityRelationship.source_entity_id == entity_id)
        else:
            filters.append(
                or_(
                    EntityRelationship.source_entity_id == entity_id,
                    EntityRelationship.target_entity_id == entity_id,
                )
            )
        if relationship_type_id is not None:
            filters.append(EntityRelationship.relationship_type_id == relationship_type_id)
        statement = select(EntityRelationship).where(*filters)
        count_statement = select(func.count(EntityRelationship.id)).where(*filters)
        items = tuple(
            (
                await self.session.scalars(
                    statement.order_by(EntityRelationship.created_at.desc(), EntityRelationship.id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total

    async def soft_delete_relationship(self, relationship_id: UUID) -> EntityRelationship | None:
        statement = (
            update(EntityRelationship)
            .where(
                EntityRelationship.id == relationship_id,
                EntityRelationship.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
            .returning(EntityRelationship)
        )
        return cast(EntityRelationship | None, await self.session.scalar(statement))
