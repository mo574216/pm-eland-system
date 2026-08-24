"""Authorized private upload and immediate inspection for staged imports."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import PurePath
from typing import BinaryIO
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DependencyUnavailableError,
    FileTooLargeError,
    FileTypeNotAllowedError,
    InvalidMetadataError,
    PermissionDeniedError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.import_job import ImportJob
from app.repositories.import_job import ImportJobRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.import_parser import ImportInspection, ImportParseError, ImportParser
from app.services.storage import StorageError, StorageProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ImportUpload:
    original_file_name: str
    content_type: str
    stream: BinaryIO
    import_profile_id: UUID | None


@dataclass(frozen=True, slots=True)
class ImportUploadResult:
    import_job_id: UUID
    status: str
    inspection: ImportInspection


class ImportJobService:
    def __init__(
        self,
        session: AsyncSession,
        actor: AuthenticatedIdentity,
        storage: StorageProvider | None,
        parser: ImportParser | None = None,
    ) -> None:
        self.session = session
        self.actor = actor
        self.storage = storage
        self.parser = parser or ImportParser()
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

    async def upload_and_inspect(
        self, workspace_id: UUID, upload: ImportUpload, *, audit: AuditContext
    ) -> ImportUploadResult:
        if self.storage is None:
            raise DependencyUnavailableError
        extension = PurePath(upload.original_file_name).suffix.lower()
        allowed = {
            ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel"},
            ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        }
        if extension not in allowed or upload.content_type.lower() not in allowed[extension]:
            raise FileTypeNotAllowedError
        await self._require_execute(workspace_id)
        try:
            inspection = await asyncio.to_thread(
                self.parser.inspect, upload.stream, filename=upload.original_file_name
            )
        except ImportParseError as error:
            if error.reason == "FILE_TOO_LARGE":
                raise FileTooLargeError from error
            raise InvalidMetadataError({"field": "file", "reason": error.reason.lower()}) from error
        upload.stream.seek(0)
        payload = upload.stream.read()
        upload.stream.seek(0)
        job_id = uuid4()
        object_key = f"workspaces/{workspace_id}/imports/{job_id}/source{extension}"
        stored = False
        try:
            async with self.session.begin():
                await self._require_execute(workspace_id)
                if upload.import_profile_id is not None:
                    profile = await self.repository.accessible_profile(
                        upload.import_profile_id, workspace_id, self.actor.user.id
                    )
                    if profile is None or profile.source_type != extension[1:].upper():
                        raise ResourceNotFoundError
                await self.storage.put_object(
                    object_key,
                    upload.stream,
                    length=len(payload),
                    content_type=upload.content_type,
                )
                stored = True
                job = ImportJob(
                    id=job_id,
                    workspace_id=workspace_id,
                    import_profile_id=upload.import_profile_id,
                    source_object_key=object_key,
                    status="UPLOADED",
                    requested_by=self.actor.user.id,
                )
                self.repository.add_job(job)
                self.repository.add_audit_log(
                    AuditLog(
                        id=uuid4(),
                        request_id=audit.request_id,
                        workspace_id=workspace_id,
                        user_id=self.actor.user.id,
                        action="IMPORT_UPLOADED",
                        resource_type="import_job",
                        resource_id=job.id,
                        before_state=None,
                        after_state={
                            "file_name": PurePath(upload.original_file_name).name,
                            "source_type": extension[1:].upper(),
                            "sheet_count": len(inspection.sheets),
                        },
                        client_ip=audit.client_ip,
                        user_agent=audit.user_agent,
                    )
                )
                await self.repository.flush()
        except StorageError as error:
            raise DependencyUnavailableError from error
        except Exception:
            if stored:
                try:
                    await self.storage.delete_object(object_key)
                except StorageError:
                    logger.exception("Failed to compensate orphaned import source object")
            raise
        return ImportUploadResult(job_id, "UPLOADED", inspection)
