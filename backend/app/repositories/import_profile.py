"""Workspace-isolated persistence for reusable import profiles."""

from typing import cast
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog
from app.models.import_job import ImportMapping, ImportProfile
from app.models.metadata import AttributeDefinition, EntityType
from app.models.workspace import WorkspaceMembership


class ImportProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_profile(self, profile: ImportProfile) -> None:
        self.session.add(profile)

    def add_mapping(self, mapping: ImportMapping) -> None:
        self.session.add(mapping)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    async def flush(self) -> None:
        await self.session.flush()

    async def accessible_profile(self, profile_id: UUID, user_id: UUID) -> ImportProfile | None:
        statement = (
            select(ImportProfile)
            .join(
                WorkspaceMembership, WorkspaceMembership.workspace_id == ImportProfile.workspace_id
            )
            .where(
                ImportProfile.id == profile_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(ImportProfile | None, await self.session.scalar(statement))

    async def list_profiles(
        self, workspace_id: UUID, user_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[ImportProfile, ...], int]:
        filters = (
            ImportProfile.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        )
        join_on = WorkspaceMembership.workspace_id == ImportProfile.workspace_id
        items = tuple(
            (
                await self.session.scalars(
                    select(ImportProfile)
                    .join(WorkspaceMembership, join_on)
                    .where(*filters)
                    .order_by(ImportProfile.name, ImportProfile.id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int(
            (
                await self.session.scalar(
                    select(func.count(ImportProfile.id))
                    .join(WorkspaceMembership, join_on)
                    .where(*filters)
                )
            )
            or 0
        )
        return items, total

    async def mappings(self, profile_id: UUID) -> tuple[ImportMapping, ...]:
        statement = (
            select(ImportMapping)
            .where(ImportMapping.import_profile_id == profile_id)
            .order_by(ImportMapping.display_order, ImportMapping.id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def replace_mappings(self, profile_id: UUID) -> None:
        await self.session.execute(
            delete(ImportMapping).where(ImportMapping.import_profile_id == profile_id)
        )

    async def entity_type_in_workspace(
        self, entity_type_id: UUID, workspace_id: UUID
    ) -> EntityType | None:
        return cast(
            EntityType | None,
            await self.session.scalar(
                select(EntityType).where(
                    EntityType.id == entity_type_id,
                    EntityType.workspace_id == workspace_id,
                    EntityType.deleted_at.is_(None),
                    EntityType.is_active.is_(True),
                )
            ),
        )

    async def active_attributes(
        self, entity_type_id: UUID, attribute_ids: frozenset[UUID]
    ) -> tuple[AttributeDefinition, ...]:
        if not attribute_ids:
            return ()
        statement = select(AttributeDefinition).where(
            AttributeDefinition.id.in_(attribute_ids),
            AttributeDefinition.entity_type_id == entity_type_id,
            AttributeDefinition.deleted_at.is_(None),
            AttributeDefinition.is_active.is_(True),
        )
        return tuple((await self.session.scalars(statement)).all())
