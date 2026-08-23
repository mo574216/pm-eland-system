"""Authorized document upload pipeline and immutable version persistence."""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import PurePath
from typing import BinaryIO
from uuid import UUID, uuid4
from zipfile import BadZipFile, ZipFile

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    DependencyUnavailableError,
    FileScanFailedError,
    FileTooLargeError,
    FileTypeNotAllowedError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.core.permissions import PermissionCode
from app.models.document import Document, DocumentVersion
from app.models.identity import AuditLog
from app.repositories.document import DocumentRecord, DocumentRepository
from app.repositories.entity import EntityRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.storage import StorageError, StorageProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentUpload:
    title: str
    description: str | None
    document_type: str | None
    original_file_name: str
    content_type: str
    stream: BinaryIO


@dataclass(frozen=True)
class DocumentVersionUpload:
    original_file_name: str
    content_type: str
    stream: BinaryIO
    comment: str | None


@dataclass(frozen=True)
class DocumentUploadResult:
    document_id: UUID
    version_id: UUID
    version_number: int
    scan_status: str


@dataclass(frozen=True)
class DocumentDownloadAccess:
    url: str
    expires_at: datetime


@dataclass(frozen=True)
class DocumentPreviewAccess:
    status: str
    preview_type: str | None
    url: str | None
    expires_at: datetime | None


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        actor: AuthenticatedIdentity,
        storage: StorageProvider | None,
        settings: Settings,
    ) -> None:
        self.session = session
        self.actor = actor
        self.storage = storage
        self.settings = settings
        self.authorization = AuthorizationService(actor)
        self.workspace_repository = WorkspaceRepository(session)
        self.entity_repository = EntityRepository(session)
        self.repository = DocumentRepository(session)

    async def create_document_with_version(
        self,
        entity_id: UUID,
        upload: DocumentUpload,
        *,
        audit: AuditContext,
    ) -> DocumentUploadResult:
        storage = self._require_storage()
        object_key: str | None = None
        stored = False
        try:
            async with self.session.begin():
                entity = await self.entity_repository.accessible_entity(
                    entity_id, self.actor.user.id
                )
                if entity is None:
                    raise ResourceNotFoundError
                await self._require_permission(entity.workspace_id)
                extension = self._validate_file_metadata(upload)
                if not upload.title.strip() or len(upload.title.strip()) > 255:
                    raise FileTypeNotAllowedError
                size, checksum = await asyncio.to_thread(
                    self._inspect_stream,
                    upload.stream,
                    self.settings.document_max_upload_bytes,
                )
                await asyncio.to_thread(self._validate_signature, upload.stream, extension)
                document_id = uuid4()
                version_id = uuid4()
                object_key = (
                    f"workspaces/{entity.workspace_id}/documents/{document_id}/"
                    f"versions/{version_id}/original"
                )
                stored = True
                try:
                    await storage.put_object(
                        object_key,
                        upload.stream,
                        length=size,
                        content_type=upload.content_type,
                    )
                except StorageError as error:
                    raise DependencyUnavailableError from error

                document = Document(
                    id=document_id,
                    workspace_id=entity.workspace_id,
                    entity_id=entity.id,
                    title=upload.title.strip(),
                    description=upload.description.strip() if upload.description else None,
                    document_type=upload.document_type.strip() if upload.document_type else None,
                    lifecycle_status="ACTIVE",
                    created_by=self.actor.user.id,
                )
                self.repository.add_document(document)
                await self.repository.flush()
                version = DocumentVersion(
                    id=version_id,
                    document_id=document.id,
                    version_number=1,
                    object_key=object_key,
                    original_file_name=upload.original_file_name,
                    content_type=upload.content_type,
                    file_extension=extension,
                    file_size_bytes=size,
                    checksum_sha256=checksum,
                    storage_provider="MINIO",
                    scan_status="PENDING",
                    preview_status=self._native_preview_status(extension),
                    uploaded_by=self.actor.user.id,
                    metadata_json={},
                )
                self.repository.add_version(version)
                await self.repository.flush()
                document.current_version_id = version.id
                document.updated_at = datetime.now(UTC)
                self.repository.add_audit_log(
                    AuditLog(
                        id=uuid4(),
                        request_id=audit.request_id,
                        workspace_id=entity.workspace_id,
                        user_id=self.actor.user.id,
                        action="DOCUMENT_CREATED",
                        resource_type="document",
                        resource_id=document.id,
                        source="API",
                        before_state=None,
                        after_state={
                            "entity_id": str(entity.id),
                            "version_id": str(version.id),
                            "version_number": 1,
                            "title": document.title,
                            "scan_status": version.scan_status,
                        },
                        client_ip=audit.client_ip,
                        user_agent=audit.user_agent,
                    )
                )
                await self.repository.flush()
            return DocumentUploadResult(document_id, version_id, 1, "PENDING")
        except Exception:
            if stored and object_key is not None:
                try:
                    await storage.delete_object(object_key)
                except StorageError:
                    logger.exception("Failed to compensate orphaned document object")
            raise

    async def add_version(
        self,
        document_id: UUID,
        upload: DocumentVersionUpload,
        *,
        audit: AuditContext,
    ) -> DocumentUploadResult:
        storage = self._require_storage()
        object_key: str | None = None
        stored = False
        try:
            async with self.session.begin():
                document = await self.repository.lock_accessible_document(
                    document_id, self.actor.user.id
                )
                if document is None:
                    raise ResourceNotFoundError
                await self._require_permission(document.workspace_id)
                extension = self._validate_file_metadata(upload)
                size, checksum = await asyncio.to_thread(
                    self._inspect_stream,
                    upload.stream,
                    self.settings.document_max_upload_bytes,
                )
                await asyncio.to_thread(self._validate_signature, upload.stream, extension)
                version_number = await self.repository.next_version_number(document.id)
                version_id = uuid4()
                object_key = (
                    f"workspaces/{document.workspace_id}/documents/{document.id}/"
                    f"versions/{version_id}/original"
                )
                stored = True
                try:
                    await storage.put_object(
                        object_key,
                        upload.stream,
                        length=size,
                        content_type=upload.content_type,
                    )
                except StorageError as error:
                    raise DependencyUnavailableError from error
                previous_version_id = document.current_version_id
                version = DocumentVersion(
                    id=version_id,
                    document_id=document.id,
                    version_number=version_number,
                    object_key=object_key,
                    original_file_name=upload.original_file_name,
                    content_type=upload.content_type,
                    file_extension=extension,
                    file_size_bytes=size,
                    checksum_sha256=checksum,
                    storage_provider="MINIO",
                    scan_status="PENDING",
                    preview_status=self._native_preview_status(extension),
                    uploaded_by=self.actor.user.id,
                    comment=upload.comment.strip() if upload.comment else None,
                    metadata_json={},
                )
                self.repository.add_version(version)
                await self.repository.flush()
                document.current_version_id = version.id
                document.updated_at = datetime.now(UTC)
                self.repository.add_audit_log(
                    AuditLog(
                        id=uuid4(),
                        request_id=audit.request_id,
                        workspace_id=document.workspace_id,
                        user_id=self.actor.user.id,
                        action="DOCUMENT_VERSION_ADDED",
                        resource_type="document",
                        resource_id=document.id,
                        source="API",
                        before_state={
                            "current_version_id": (
                                str(previous_version_id) if previous_version_id else None
                            )
                        },
                        after_state={
                            "current_version_id": str(version.id),
                            "version_number": version.version_number,
                            "scan_status": version.scan_status,
                        },
                        client_ip=audit.client_ip,
                        user_agent=audit.user_agent,
                    )
                )
                await self.repository.flush()
            return DocumentUploadResult(
                document.id, version.id, version.version_number, version.scan_status
            )
        except Exception:
            if stored and object_key is not None:
                try:
                    await storage.delete_object(object_key)
                except StorageError:
                    logger.exception("Failed to compensate orphaned document-version object")
            raise

    async def _require_permission(self, workspace_id: UUID) -> None:
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if PermissionCode.DOCUMENT_UPLOAD.value not in effective:
            raise PermissionDeniedError

    async def get_download_access(self, version_id: UUID) -> DocumentDownloadAccess:
        storage = self._require_storage()
        record = await self.repository.accessible_version(version_id, self.actor.user.id)
        if record is None:
            raise ResourceNotFoundError
        version = record.version
        await self._require_read_permission(record.document.workspace_id)
        if version.scan_status not in self.settings.document_download_allowed_scan_statuses:
            raise FileScanFailedError
        try:
            url = await storage.create_download_url(version.object_key)
        except StorageError as error:
            raise DependencyUnavailableError from error
        return DocumentDownloadAccess(
            url=url,
            expires_at=datetime.now(UTC)
            + timedelta(seconds=self.settings.storage_presigned_expiry_seconds),
        )

    async def get_preview_access(self, version_id: UUID) -> DocumentPreviewAccess:
        storage = self._require_storage()
        record = await self.repository.accessible_version(version_id, self.actor.user.id)
        if record is None:
            raise ResourceNotFoundError
        version = record.version
        await self._require_read_permission(record.document.workspace_id)
        if version.scan_status not in self.settings.document_download_allowed_scan_statuses:
            raise FileScanFailedError
        preview_type = self._native_preview_type(version.file_extension)
        if preview_type is None:
            return DocumentPreviewAccess("NOT_REQUESTED", None, None, None)
        if version.preview_status != "READY":
            return DocumentPreviewAccess(version.preview_status, preview_type, None, None)
        try:
            url = await storage.create_download_url(version.object_key)
        except StorageError as error:
            raise DependencyUnavailableError from error
        return DocumentPreviewAccess(
            "READY",
            preview_type,
            url,
            datetime.now(UTC) + timedelta(seconds=self.settings.storage_presigned_expiry_seconds),
        )

    async def list_entity_documents(
        self, entity_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[DocumentRecord, ...], int]:
        entity = await self.entity_repository.accessible_entity(entity_id, self.actor.user.id)
        if entity is None:
            raise ResourceNotFoundError
        await self._require_read_permission(entity.workspace_id)
        return await self.repository.list_entity_documents(
            entity.workspace_id,
            entity.id,
            page=page,
            page_size=page_size,
        )

    async def get_document(self, document_id: UUID) -> DocumentRecord:
        record = await self.repository.accessible_document_record(document_id, self.actor.user.id)
        if record is None:
            raise ResourceNotFoundError
        await self._require_read_permission(record.document.workspace_id)
        return record

    async def list_versions(
        self, document_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[DocumentVersion, ...], int]:
        record = await self.get_document(document_id)
        return await self.repository.list_versions(
            record.document.id, page=page, page_size=page_size
        )

    async def _require_read_permission(self, workspace_id: UUID) -> None:
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if PermissionCode.DOCUMENT_READ.value not in effective:
            raise PermissionDeniedError

    def _require_storage(self) -> StorageProvider:
        if self.storage is None:
            raise DependencyUnavailableError
        return self.storage

    @staticmethod
    def _native_preview_type(extension: str | None) -> str | None:
        if extension == ".pdf":
            return "PDF"
        if extension in {".png", ".jpg", ".jpeg"}:
            return "IMAGE"
        return None

    @classmethod
    def _native_preview_status(cls, extension: str) -> str:
        return "READY" if cls._native_preview_type(extension) is not None else "NOT_REQUESTED"

    def _validate_file_metadata(self, upload: DocumentUpload | DocumentVersionUpload) -> str:
        filename = upload.original_file_name
        if (
            not filename
            or len(filename) > 500
            or "\x00" in filename
            or "/" in filename
            or "\\" in filename
            or PurePath(filename).name != filename
        ):
            raise FileTypeNotAllowedError
        extension = PurePath(filename).suffix.lower()
        allowed_mimes = self.settings.document_allowed_mime_by_extension.get(extension)
        normalized_content_type = upload.content_type.partition(";")[0].strip().lower()
        if allowed_mimes is None or normalized_content_type not in allowed_mimes:
            raise FileTypeNotAllowedError
        return extension

    @staticmethod
    def _inspect_stream(stream: BinaryIO, maximum: int) -> tuple[int, str]:
        digest = hashlib.sha256()
        size = 0
        stream.seek(0)
        while chunk := stream.read(min(1024 * 1024, maximum + 1 - size)):
            size += len(chunk)
            if size > maximum:
                stream.seek(0)
                raise FileTooLargeError
            digest.update(chunk)
        stream.seek(0)
        if size == 0:
            raise FileTypeNotAllowedError
        return size, digest.hexdigest()

    @staticmethod
    def _validate_signature(stream: BinaryIO, extension: str) -> None:
        stream.seek(0)
        header = stream.read(16)
        stream.seek(0)
        valid = True
        if extension == ".pdf":
            valid = header.startswith(b"%PDF-")
        elif extension == ".png":
            valid = header.startswith(b"\x89PNG\r\n\x1a\n")
        elif extension in {".jpg", ".jpeg"}:
            valid = header.startswith(b"\xff\xd8\xff")
        elif extension in {".xml", ".bpmn", ".svg"}:
            valid = header.lstrip(b"\xef\xbb\xbf\x00\t\r\n ").startswith(b"<")
        elif extension in {".docx", ".xlsx"}:
            try:
                with ZipFile(stream) as archive:
                    names = set(archive.namelist())
                expected_prefix = "word/" if extension == ".docx" else "xl/"
                valid = "[Content_Types].xml" in names and any(
                    name.startswith(expected_prefix) for name in names
                )
            except (BadZipFile, OSError):
                valid = False
            finally:
                stream.seek(0)
        if not valid:
            raise FileTypeNotAllowedError
