"""Workspace-isolated staged import-job persistence."""

from typing import cast
from uuid import UUID

from sqlalchemy import delete, func, select
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

    async def accessible_conflict(
        self, job_id: UUID, conflict_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> ImportConflict | None:
        statement = (
            select(ImportConflict)
            .join(ImportJob, ImportJob.id == ImportConflict.import_job_id)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == ImportJob.workspace_id)
            .where(
                ImportConflict.id == conflict_id,
                ImportConflict.import_job_id == job_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return cast(ImportConflict | None, await self.session.scalar(statement))

    async def list_conflicts(
        self,
        job_id: UUID,
        *,
        page: int,
        page_size: int,
        resolution_status: str,
    ) -> tuple[tuple[ImportConflict, ...], int]:
        filters = [ImportConflict.import_job_id == job_id]
        if resolution_status == "UNRESOLVED":
            filters.append(ImportConflict.resolution.is_(None))
        elif resolution_status == "RESOLVED":
            filters.append(ImportConflict.resolution.is_not(None))
        elif resolution_status != "ALL":
            filters.append(ImportConflict.resolution == resolution_status)
        statement = select(ImportConflict).where(*filters)
        count_statement = select(func.count(ImportConflict.id)).where(*filters)
        items = tuple(
            (
                await self.session.scalars(
                    statement.order_by(
                        ImportConflict.row_number,
                        ImportConflict.attribute_key,
                        ImportConflict.id,
                    )
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total

    async def conflicts_by_ids(
        self, job_id: UUID, conflict_ids: frozenset[UUID]
    ) -> tuple[ImportConflict, ...]:
        if not conflict_ids:
            return ()
        statement = (
            select(ImportConflict)
            .where(
                ImportConflict.import_job_id == job_id,
                ImportConflict.id.in_(conflict_ids),
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def unresolved_conflict_count(self, job_id: UUID) -> int:
        statement = select(func.count(ImportConflict.id)).where(
            ImportConflict.import_job_id == job_id,
            ImportConflict.resolution.is_(None),
        )
        return int((await self.session.scalar(statement)) or 0)

    async def all_conflicts(self, job_id: UUID) -> tuple[ImportConflict, ...]:
        statement = select(ImportConflict).where(ImportConflict.import_job_id == job_id)
        return tuple((await self.session.scalars(statement)).all())

    async def job_by_idempotency_key(
        self, workspace_id: UUID, idempotency_key: str
    ) -> ImportJob | None:
        statement = select(ImportJob).where(
            ImportJob.workspace_id == workspace_id,
            ImportJob.idempotency_key == idempotency_key,
        )
        return cast(ImportJob | None, await self.session.scalar(statement))
