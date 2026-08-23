"""Authorized first-document-version upload pipeline tests."""

import hashlib
from datetime import UTC, datetime
from io import BytesIO
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    FileScanFailedError,
    FileTooLargeError,
    FileTypeNotAllowedError,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.core.permissions import PermissionCode
from app.models.document import Document, DocumentVersion
from app.models.entity import EntityObject
from app.models.identity import AuditLog, User
from app.repositories.document import DocumentRecord, DocumentRepository, DocumentVersionRecord
from app.repositories.entity import EntityRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.document import DocumentService, DocumentUpload, DocumentVersionUpload
from app.services.storage import StorageProvider


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()


class FakeEntityRepository:
    def __init__(self, entity: EntityObject | None) -> None:
        self.entity = entity

    async def accessible_entity(self, _: UUID, __: UUID) -> EntityObject | None:
        return self.entity


class FakeWorkspaceRepository:
    def __init__(self, permissions: tuple[str, ...]) -> None:
        self.permissions = permissions

    async def workspace_permission_codes(self, _: UUID, __: UUID) -> tuple[str, ...]:
        return self.permissions


class FakeDocumentRepository:
    def __init__(self, *, fail_flush: int | None = None) -> None:
        self.documents: list[Document] = []
        self.versions: list[DocumentVersion] = []
        self.audit_logs: list[AuditLog] = []
        self.flush_count = 0
        self.fail_flush = fail_flush
        self.locked_document: Document | None = None
        self.lock_calls: list[UUID] = []
        self.accessible_record: DocumentVersionRecord | None = None
        self.accessible_document: DocumentRecord | None = None

    def add_document(self, value: Document) -> None:
        self.documents.append(value)

    def add_version(self, value: DocumentVersion) -> None:
        self.versions.append(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.audit_logs.append(value)

    async def flush(self) -> None:
        self.flush_count += 1
        if self.flush_count == self.fail_flush:
            raise RuntimeError("database unavailable")

    async def lock_accessible_document(self, document_id: UUID, _: UUID) -> Document | None:
        self.lock_calls.append(document_id)
        return self.locked_document

    async def next_version_number(self, _: UUID) -> int:
        return max((version.version_number for version in self.versions), default=0) + 1

    async def accessible_version(self, _: UUID, __: UUID) -> DocumentVersionRecord | None:
        return self.accessible_record

    async def list_entity_documents(
        self, _: UUID, __: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[DocumentRecord, ...], int]:
        del page, page_size
        return (() if self.accessible_document is None else (self.accessible_document,)), int(
            self.accessible_document is not None
        )

    async def accessible_document_record(self, _: UUID, __: UUID) -> DocumentRecord | None:
        return self.accessible_document

    async def list_versions(
        self, _: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[DocumentVersion, ...], int]:
        del page, page_size
        return tuple(self.versions), len(self.versions)


class FakeStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, int, str]] = []
        self.deleted: list[str] = []
        self.downloads: list[str] = []

    async def put_object(
        self, object_key: str, data: object, *, length: int, content_type: str
    ) -> None:
        stream = cast(BytesIO, data)
        self.uploads.append((object_key, stream.read(), length, content_type))

    async def delete_object(self, object_key: str) -> None:
        self.deleted.append(object_key)

    async def object_exists(self, _: str) -> bool:
        return False

    async def create_download_url(self, object_key: str) -> str:
        self.downloads.append(object_key)
        return "https://storage.test/exact-private-object"

    async def create_upload_url(self, _: str) -> str:
        return "unused"


def identity(*permissions: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="document-analyst",
        email="documents@example.test",
        password_hash="unused-document-test-hash",  # noqa: S106
    )
    return AuthenticatedIdentity(
        user=user,
        roles=("ANALYST",),
        permissions=tuple(permission.value for permission in permissions),
    )


def build_service(
    *,
    permissions: tuple[str, ...] = (),
    maximum: int = 1024,
    fail_flush: int | None = None,
) -> tuple[DocumentService, FakeDocumentRepository, FakeStorage, EntityObject]:
    actor = identity()
    workspace_id = uuid4()
    entity = EntityObject(
        id=uuid4(),
        workspace_id=workspace_id,
        entity_type_id=uuid4(),
        name="Generic entity",
    )
    storage = FakeStorage()
    service = DocumentService(
        cast(AsyncSession, FakeSession()),
        actor,
        cast(StorageProvider, storage),
        Settings(document_max_upload_bytes=maximum),
    )
    repository = FakeDocumentRepository(fail_flush=fail_flush)
    service.entity_repository = cast(EntityRepository, FakeEntityRepository(entity))
    service.workspace_repository = cast(WorkspaceRepository, FakeWorkspaceRepository(permissions))
    service.repository = cast(DocumentRepository, repository)
    return service, repository, storage, entity


def upload(content: bytes = b"%PDF-1.7\nsafe pdf") -> DocumentUpload:
    return DocumentUpload(
        title="Architecture report",
        description="First approved draft",
        document_type="REPORT",
        original_file_name="report.pdf",
        content_type="application/pdf",
        stream=BytesIO(content),
    )


def audit() -> AuditContext:
    return AuditContext(uuid4(), "127.0.0.1", "test-agent")


@pytest.mark.asyncio
async def test_first_version_uses_generated_key_checksum_and_audit() -> None:
    service, repository, storage, entity = build_service(
        permissions=(PermissionCode.DOCUMENT_UPLOAD.value,)
    )

    result = await service.create_document_with_version(entity.id, upload(), audit=audit())

    assert result.version_number == 1
    assert result.scan_status == "PENDING"
    document = repository.documents[0]
    version = repository.versions[0]
    assert document.workspace_id == entity.workspace_id
    assert document.entity_id == entity.id
    assert document.current_version_id == version.id
    assert version.document_id == document.id
    assert version.checksum_sha256 == hashlib.sha256(b"%PDF-1.7\nsafe pdf").hexdigest()
    assert version.original_file_name == "report.pdf"
    assert version.preview_status == "READY"
    assert "report.pdf" not in version.object_key
    assert str(entity.workspace_id) in version.object_key
    assert storage.uploads == [(version.object_key, b"%PDF-1.7\nsafe pdf", 17, "application/pdf")]
    assert repository.audit_logs[0].action == "DOCUMENT_CREATED"
    assert repository.audit_logs[0].workspace_id == entity.workspace_id


@pytest.mark.asyncio
async def test_permission_and_file_policy_are_authoritative_before_storage() -> None:
    service, _, storage, entity = build_service()
    with pytest.raises(PermissionDeniedError):
        await service.create_document_with_version(entity.id, upload(), audit=audit())
    assert storage.uploads == []

    service, _, storage, entity = build_service(permissions=(PermissionCode.DOCUMENT_UPLOAD.value,))
    unsafe = upload()
    unsafe = DocumentUpload(**{**unsafe.__dict__, "original_file_name": "../report.pdf"})
    with pytest.raises(FileTypeNotAllowedError):
        await service.create_document_with_version(entity.id, unsafe, audit=audit())
    assert storage.uploads == []

    with pytest.raises(FileTypeNotAllowedError):
        await service.create_document_with_version(entity.id, upload(b"not a pdf"), audit=audit())
    assert storage.uploads == []


@pytest.mark.asyncio
async def test_size_limit_and_database_failure_do_not_leave_an_object() -> None:
    service, _, storage, entity = build_service(
        permissions=(PermissionCode.DOCUMENT_UPLOAD.value,), maximum=4
    )
    with pytest.raises(FileTooLargeError):
        await service.create_document_with_version(entity.id, upload(b"12345"), audit=audit())
    assert storage.uploads == []

    service, _, storage, entity = build_service(
        permissions=(PermissionCode.DOCUMENT_UPLOAD.value,), fail_flush=1
    )
    with pytest.raises(RuntimeError, match="database unavailable"):
        await service.create_document_with_version(entity.id, upload(), audit=audit())
    assert storage.deleted == [storage.uploads[0][0]]


@pytest.mark.asyncio
async def test_new_version_locks_document_preserves_old_version_and_advances_current() -> None:
    service, repository, storage, entity = build_service(
        permissions=(PermissionCode.DOCUMENT_UPLOAD.value,)
    )
    old_version_id = uuid4()
    document = Document(
        id=uuid4(),
        workspace_id=entity.workspace_id,
        entity_id=entity.id,
        title="Architecture report",
        lifecycle_status="ACTIVE",
        current_version_id=old_version_id,
        created_by=service.actor.user.id,
    )
    old_version = DocumentVersion(
        id=old_version_id,
        document_id=document.id,
        version_number=1,
        object_key="workspaces/original",
        original_file_name="report-v1.pdf",
        content_type="application/pdf",
        file_extension=".pdf",
        file_size_bytes=10,
        checksum_sha256="0" * 64,
        uploaded_by=service.actor.user.id,
        metadata_json={},
    )
    repository.locked_document = document
    repository.versions.append(old_version)

    result = await service.add_version(
        document.id,
        DocumentVersionUpload(
            original_file_name="report-v2.pdf",
            content_type="application/pdf",
            stream=BytesIO(b"%PDF-1.7\nversion two"),
            comment="Second revision",
        ),
        audit=audit(),
    )

    assert repository.lock_calls == [document.id]
    assert result.version_number == 2
    assert repository.versions[0] is old_version
    assert repository.versions[0].object_key == "workspaces/original"
    new_version = repository.versions[1]
    assert new_version.version_number == 2
    assert new_version.comment == "Second revision"
    assert document.current_version_id == new_version.id
    assert storage.uploads[0][0] == new_version.object_key
    audit_log = repository.audit_logs[0]
    assert audit_log.action == "DOCUMENT_VERSION_ADDED"
    assert audit_log.before_state == {"current_version_id": str(old_version_id)}


@pytest.mark.asyncio
async def test_download_requires_access_read_permission_and_allowed_scan_state() -> None:
    service, repository, storage, entity = build_service(
        permissions=(PermissionCode.DOCUMENT_READ.value,)
    )
    version_id = uuid4()
    document = Document(
        id=uuid4(),
        workspace_id=entity.workspace_id,
        entity_id=entity.id,
        title="Architecture report",
        lifecycle_status="ACTIVE",
        current_version_id=version_id,
        created_by=service.actor.user.id,
    )
    version = DocumentVersion(
        id=version_id,
        document_id=document.id,
        version_number=1,
        object_key="workspaces/exact-version/original",
        original_file_name="report.pdf",
        content_type="application/pdf",
        file_extension=".pdf",
        file_size_bytes=10,
        checksum_sha256="0" * 64,
        scan_status="PENDING",
        preview_status="READY",
        uploaded_by=service.actor.user.id,
        metadata_json={},
    )

    with pytest.raises(ResourceNotFoundError):
        await service.get_download_access(version.id)
    repository.accessible_record = DocumentVersionRecord(version, document)
    with pytest.raises(FileScanFailedError):
        await service.get_download_access(version.id)
    with pytest.raises(FileScanFailedError):
        await service.get_preview_access(version.id)
    assert storage.downloads == []

    version.scan_status = "CLEAN"
    before = datetime.now(UTC)
    access = await service.get_download_access(version.id)
    assert access.url == "https://storage.test/exact-private-object"
    assert storage.downloads == [version.object_key]
    assert 599 <= (access.expires_at - before).total_seconds() <= 601

    preview = await service.get_preview_access(version.id)
    assert preview.status == "READY"
    assert preview.preview_type == "PDF"
    assert preview.url == "https://storage.test/exact-private-object"
    assert preview.expires_at is not None
    assert storage.downloads == [version.object_key, version.object_key]

    version.file_extension = ".png"
    image_preview = await service.get_preview_access(version.id)
    assert image_preview.preview_type == "IMAGE"

    version.file_extension = ".svg"
    unsupported = await service.get_preview_access(version.id)
    assert unsupported.status == "NOT_REQUESTED"
    assert unsupported.url is None
    assert storage.downloads == [version.object_key, version.object_key, version.object_key]

    denied, denied_repository, denied_storage, _ = build_service()
    denied_repository.accessible_record = DocumentVersionRecord(version, document)
    with pytest.raises(PermissionDeniedError):
        await denied.get_download_access(version.id)
    assert denied_storage.downloads == []


@pytest.mark.asyncio
async def test_metadata_and_history_reads_are_workspace_permission_scoped() -> None:
    service, repository, storage, entity = build_service(
        permissions=(PermissionCode.DOCUMENT_READ.value,)
    )
    document = Document(
        id=uuid4(),
        workspace_id=entity.workspace_id,
        entity_id=entity.id,
        title="Architecture report",
        lifecycle_status="ACTIVE",
        created_by=service.actor.user.id,
    )
    version = DocumentVersion(
        id=uuid4(),
        document_id=document.id,
        version_number=1,
        object_key="private/not-returned",
        original_file_name="report.pdf",
        content_type="application/pdf",
        file_extension=".pdf",
        file_size_bytes=10,
        scan_status="PENDING",
        uploaded_by=service.actor.user.id,
        metadata_json={},
    )
    document.current_version_id = version.id
    repository.accessible_document = DocumentRecord(document, version)
    repository.versions.append(version)

    items, total = await service.list_entity_documents(entity.id, page=1, page_size=50)
    history, history_total = await service.list_versions(document.id, page=1, page_size=50)
    assert items == (repository.accessible_document,)
    assert total == 1
    assert history == (version,)
    assert history_total == 1
    assert storage.downloads == []

    denied, denied_repository, _, denied_entity = build_service()
    denied_repository.accessible_document = repository.accessible_document
    with pytest.raises(PermissionDeniedError):
        await denied.list_entity_documents(denied_entity.id, page=1, page_size=50)
