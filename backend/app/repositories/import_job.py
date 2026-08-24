"""Workspace-isolated staged import-job persistence."""

from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog
from app.models.import_job import ImportJob, ImportProfile
from app.models.workspace import WorkspaceMembership


class ImportJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_job(self, job: ImportJob) -> None:
        self.session.add(job)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

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
