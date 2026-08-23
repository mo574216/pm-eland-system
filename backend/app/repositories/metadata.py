"""Workspace-isolated metadata persistence operations."""

from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import WorkspaceMembership


class MetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_entity_type(self, entity_type: EntityType) -> None:
        self.session.add(entity_type)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    async def flush(self) -> None:
        await self.session.flush()

    async def entity_type_by_key(self, workspace_id: UUID, key: str) -> EntityType | None:
        statement = select(EntityType).where(
            EntityType.workspace_id == workspace_id,
            EntityType.key == key,
            EntityType.deleted_at.is_(None),
        )
        return cast(EntityType | None, await self.session.scalar(statement))

    async def accessible_entity_type(
        self, entity_type_id: UUID, user_id: UUID
    ) -> EntityType | None:
        statement = (
            select(EntityType)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityType.workspace_id,
            )
            .where(
                EntityType.id == entity_type_id,
                EntityType.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(EntityType | None, await self.session.scalar(statement))

    async def list_entity_types(
        self,
        workspace_id: UUID,
        user_id: UUID,
        *,
        page: int,
        page_size: int,
        active: bool | None,
        search: str | None,
    ) -> tuple[tuple[EntityType, ...], int]:
        filters = [
            EntityType.workspace_id == workspace_id,
            EntityType.deleted_at.is_(None),
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        ]
        if active is not None:
            filters.append(EntityType.is_active.is_(active))
        if search is not None:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    EntityType.key.ilike(pattern),
                    EntityType.name.ilike(pattern),
                    EntityType.plural_name.ilike(pattern),
                )
            )
        join_condition = WorkspaceMembership.workspace_id == EntityType.workspace_id
        statement = select(EntityType).join(WorkspaceMembership, join_condition)
        count_statement = select(func.count(EntityType.id)).join(
            WorkspaceMembership, join_condition
        )
        items = tuple(
            (
                await self.session.scalars(
                    statement.where(*filters)
                    .order_by(EntityType.name, EntityType.id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int((await self.session.scalar(count_statement.where(*filters))) or 0)
        return items, total

    async def update_entity_type(
        self, entity_type_id: UUID, expected_version: int, values: dict[str, object]
    ) -> EntityType | None:
        statement = (
            update(EntityType)
            .where(
                EntityType.id == entity_type_id,
                EntityType.version == expected_version,
                EntityType.deleted_at.is_(None),
            )
            .values(**values, version=EntityType.version + 1, updated_at=func.now())
            .returning(EntityType)
        )
        return cast(EntityType | None, await self.session.scalar(statement))

    async def archive_entity_type(
        self, entity_type_id: UUID, expected_version: int
    ) -> EntityType | None:
        return await self.update_entity_type(
            entity_type_id,
            expected_version,
            {"is_active": False, "deleted_at": func.now()},
        )

    def add_attribute(self, attribute: AttributeDefinition) -> None:
        self.session.add(attribute)

    async def attribute_by_key(self, entity_type_id: UUID, key: str) -> AttributeDefinition | None:
        statement = select(AttributeDefinition).where(
            AttributeDefinition.entity_type_id == entity_type_id,
            AttributeDefinition.key == key,
            AttributeDefinition.deleted_at.is_(None),
        )
        return cast(AttributeDefinition | None, await self.session.scalar(statement))

    async def accessible_attribute(
        self, attribute_id: UUID, user_id: UUID
    ) -> tuple[AttributeDefinition, EntityType] | None:
        statement = (
            select(AttributeDefinition, EntityType)
            .join(EntityType, EntityType.id == AttributeDefinition.entity_type_id)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == EntityType.workspace_id,
            )
            .where(
                AttributeDefinition.id == attribute_id,
                AttributeDefinition.deleted_at.is_(None),
                EntityType.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        row = (await self.session.execute(statement)).one_or_none()
        if row is None:
            return None
        return cast(tuple[AttributeDefinition, EntityType], tuple(row))

    async def list_attributes(self, entity_type_id: UUID) -> tuple[AttributeDefinition, ...]:
        statement = (
            select(AttributeDefinition)
            .where(
                AttributeDefinition.entity_type_id == entity_type_id,
                AttributeDefinition.deleted_at.is_(None),
                AttributeDefinition.is_active.is_(True),
            )
            .order_by(
                AttributeDefinition.display_order,
                AttributeDefinition.label,
                AttributeDefinition.id,
            )
        )
        return tuple((await self.session.scalars(statement)).all())

    async def update_attribute(
        self, attribute_id: UUID, expected_version: int, values: dict[str, object]
    ) -> AttributeDefinition | None:
        statement = (
            update(AttributeDefinition)
            .where(
                AttributeDefinition.id == attribute_id,
                AttributeDefinition.version == expected_version,
                AttributeDefinition.deleted_at.is_(None),
            )
            .values(
                **values,
                version=AttributeDefinition.version + 1,
                updated_at=func.now(),
            )
            .returning(AttributeDefinition)
        )
        return cast(AttributeDefinition | None, await self.session.scalar(statement))

    async def deactivate_attribute(
        self, attribute_id: UUID, expected_version: int
    ) -> AttributeDefinition | None:
        return await self.update_attribute(
            attribute_id,
            expected_version,
            {"is_active": False, "deleted_at": func.now()},
        )

    async def entity_type_in_workspace(
        self, entity_type_id: UUID, workspace_id: UUID
    ) -> EntityType | None:
        statement = select(EntityType).where(
            EntityType.id == entity_type_id,
            EntityType.workspace_id == workspace_id,
            EntityType.deleted_at.is_(None),
        )
        return cast(EntityType | None, await self.session.scalar(statement))
