"""Workspace-isolated staged import-job persistence."""

from typing import cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import EntityObject
from app.models.identity import AuditLog
from app.models.import_job import ImportConflict, ImportJob, ImportMapping, ImportProfile
from app.models.workspace import WorkspaceMembership


class ImportJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_job(self, job: ImportJob) -> None:
        self.session.add(job)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    def add_conflict(self, conflict: ImportConflict) -> None:
        self.session.add(conflict)

    async def flush(self) -> None:
        await self.session.flush()

    async def accessible_profile(
        self, profile_id: UUID, workspace_id: UUID, user_id: UUID
    ) -> ImportProfile | None:
        statement = (
            select(ImportProfile)
            .join(
                WorkspaceMembership, WorkspaceMembership.workspace_id == ImportProfile.workspace_id
            )
            .where(
                ImportProfile.id == profile_id,
                ImportProfile.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(ImportProfile | None, await self.session.scalar(statement))

    async def accessible_job(
        self, job_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> ImportJob | None:
        statement = (
            select(ImportJob)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == ImportJob.workspace_id)
            .where(
                ImportJob.id == job_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return cast(ImportJob | None, await self.session.scalar(statement))

    async def profile_mappings(self, profile_id: UUID) -> tuple[ImportMapping, ...]:
        statement = (
            select(ImportMapping)
            .where(ImportMapping.import_profile_id == profile_id)
            .order_by(ImportMapping.display_order, ImportMapping.id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def entities_for_type(
        self, workspace_id: UUID, entity_type_id: UUID
    ) -> tuple[EntityObject, ...]:
        statement = select(EntityObject).where(
            EntityObject.workspace_id == workspace_id,
            EntityObject.entity_type_id == entity_type_id,
            EntityObject.deleted_at.is_(None),
            EntityObject.status != "DELETED",
        )
        return tuple((await self.session.scalars(statement)).all())

    async def clear_conflicts(self, job_id: UUID) -> None:
        await self.session.execute(
            delete(ImportConflict).where(ImportConflict.import_job_id == job_id)
        )
