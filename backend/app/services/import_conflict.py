"""Authorized explicit conflict decisions for staged imports."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.import_job import ImportConflict, ImportJob
from app.repositories.import_job import ImportJobRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.import_job import ImportConflictResolution
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


@dataclass(frozen=True, slots=True)
class ImportConflictPage:
    items: tuple[ImportConflict, ...]
    page: int
    page_size: int
    total: int
    unresolved: int


@dataclass(frozen=True, slots=True)
class ImportResolutionResult:
    import_job_id: UUID
    status: str
    resolved: int
    unresolved: int


class ImportConflictService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = ImportJobRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

    async def _require_execute(self, workspace_id: UUID) -> None:
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
        if PermissionCode.IMPORT_EXECUTE.value not in effective:
            raise PermissionDeniedError

    async def list_conflicts(
        self,
        job_id: UUID,
        *,
        page: int,
        page_size: int,
        resolution_status: str,
    ) -> ImportConflictPage:
        job = await self.repository.accessible_job(job_id, self.actor.user.id)
        if job is None:
            raise ResourceNotFoundError
        await self._require_execute(job.workspace_id)
        items, total = await self.repository.list_conflicts(
            job.id,
            page=page,
            page_size=page_size,
            resolution_status=resolution_status,
        )
        unresolved = await self.repository.unresolved_conflict_count(job.id)
        return ImportConflictPage(items, page, page_size, total, unresolved)

    async def resolve_one(
        self,
        job_id: UUID,
        conflict_id: UUID,
        resolution: ImportConflictResolution,
        *,
        audit: AuditContext,
    ) -> ImportResolutionResult:
        async with self.session.begin():
            job = await self._reviewable_job(job_id)
            conflict = await self.repository.accessible_conflict(
                job.id, conflict_id, self.actor.user.id, lock=True
            )
            if conflict is None:
                raise ResourceNotFoundError
            before = conflict.resolution
            self._apply_resolution(conflict, resolution)
            await self.repository.flush()
            unresolved = await self.repository.unresolved_conflict_count(job.id)
            self._update_status(job, unresolved)
            self.repository.add_audit_log(
                self._audit(
                    job,
                    "IMPORT_CONFLICT_RESOLVED",
                    {
                        "conflict_id": str(conflict.id),
                        "resolution": before,
                    },
                    {
                        "conflict_id": str(conflict.id),
                        "resolution": resolution,
                        "unresolved": unresolved,
                    },
                    audit,
                )
            )
            await self.repository.flush()
        return ImportResolutionResult(job.id, job.status, 1, unresolved)

    async def resolve_bulk(
        self,
        job_id: UUID,
        conflict_ids: tuple[UUID, ...],
        resolution: ImportConflictResolution,
        *,
        audit: AuditContext,
    ) -> ImportResolutionResult:
        unique_ids = frozenset(conflict_ids)
        if len(unique_ids) != len(conflict_ids):
            raise ResourceConflictError
        async with self.session.begin():
            job = await self._reviewable_job(job_id)
            conflicts = await self.repository.conflicts_by_ids(job.id, unique_ids)
            if len(conflicts) != len(unique_ids):
                raise ResourceNotFoundError
            for conflict in conflicts:
                self._apply_resolution(conflict, resolution)
            await self.repository.flush()
            unresolved = await self.repository.unresolved_conflict_count(job.id)
            self._update_status(job, unresolved)
            self.repository.add_audit_log(
                self._audit(
                    job,
                    "IMPORT_CONFLICTS_RESOLVED_BULK",
                    None,
                    {
                        "conflict_ids": sorted(str(item) for item in unique_ids),
                        "resolution": resolution,
                        "resolved": len(conflicts),
                        "unresolved": unresolved,
                    },
                    audit,
                )
            )
            await self.repository.flush()
        return ImportResolutionResult(job.id, job.status, len(conflicts), unresolved)

    async def _reviewable_job(self, job_id: UUID) -> ImportJob:
        job = await self.repository.accessible_job(job_id, self.actor.user.id, lock=True)
        if job is None:
            raise ResourceNotFoundError
        await self._require_execute(job.workspace_id)
        if job.status not in {"READY_FOR_REVIEW", "READY_TO_COMMIT"}:
            raise ResourceConflictError
        return job

    def _apply_resolution(
        self, conflict: ImportConflict, resolution: ImportConflictResolution
    ) -> None:
        conflict.resolution = resolution
        conflict.resolved_by = self.actor.user.id
        conflict.resolved_at = datetime.now(UTC)

    @staticmethod
    def _update_status(job: ImportJob, unresolved: int) -> None:
        job.status = "READY_TO_COMMIT" if unresolved == 0 else "READY_FOR_REVIEW"

    def _audit(
        self,
        job: ImportJob,
        action: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=job.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="import_job",
            resource_id=job.id,
            before_state=before,
            after_state=after,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )
