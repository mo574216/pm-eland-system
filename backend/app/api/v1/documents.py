"""Authorized document upload endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.dependencies.storage import get_storage_provider
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.models.document import DocumentVersion
from app.repositories.document import DocumentRecord
from app.schemas.document import (
    DocumentDownloadAccessResponse,
    DocumentListResponse,
    DocumentPreviewAccessResponse,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentVersionListResponse,
    DocumentVersionResponse,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.document import DocumentService, DocumentUpload, DocumentVersionUpload
from app.services.storage import StorageProvider

router = APIRouter(tags=["Documents"])


def _version_response(version: DocumentVersion) -> DocumentVersionResponse:
    return DocumentVersionResponse(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        original_file_name=version.original_file_name,
        content_type=version.content_type,
        file_extension=version.file_extension,
        file_size_bytes=version.file_size_bytes,
        checksum_sha256=version.checksum_sha256,
        scan_status=version.scan_status,
        preview_status=version.preview_status,
        uploaded_by=version.uploaded_by,
        uploaded_at=version.uploaded_at,
        comment=version.comment,
        metadata=version.metadata_json,
    )


def _document_response(record: DocumentRecord) -> DocumentResponse:
    document = record.document
    return DocumentResponse(
        id=document.id,
        workspace_id=document.workspace_id,
        entity_id=document.entity_id,
        title=document.title,
        description=document.description,
        document_type=document.document_type,
        lifecycle_status=document.lifecycle_status,
        current_version_id=document.current_version_id,
        current_version=(
            _version_response(record.current_version) if record.current_version else None
        ),
        created_by=document.created_by,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post(
    "/entities/{entity_id}/documents",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    entity_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=1, max_length=255)],
    description: Annotated[str | None, Form(max_length=10_000)] = None,
    document_type: Annotated[str | None, Form(max_length=100)] = None,
) -> dict[str, object]:
    result = await DocumentService(
        session,
        actor,
        storage,
        request.app.state.settings,
    ).create_document_with_version(
        entity_id,
        DocumentUpload(
            title=title,
            description=description,
            document_type=document_type,
            original_file_name=file.filename or "",
            content_type=file.content_type or "application/octet-stream",
            stream=file.file,
        ),
        audit=AuditContext(
            request_id=UUID(get_request_id()),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )
    response = DocumentUploadResponse(
        document_id=result.document_id,
        version_id=result.version_id,
        version_number=1,
        scan_status="PENDING",
    )
    return success_envelope(response.model_dump(mode="json"))


@router.get("/entities/{entity_id}/documents")
async def list_entity_documents(
    entity_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    items, total = await DocumentService(
        session, actor, None, request.app.state.settings
    ).list_entity_documents(entity_id, page=page, page_size=page_size)
    response = DocumentListResponse(
        items=tuple(_document_response(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))


@router.get("/documents/{document_id}")
async def get_document(
    document_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await DocumentService(session, actor, None, request.app.state.settings).get_document(
        document_id
    )
    return success_envelope(_document_response(record).model_dump(mode="json"))


@router.get("/documents/{document_id}/versions")
async def list_document_versions(
    document_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    items, total = await DocumentService(
        session, actor, None, request.app.state.settings
    ).list_versions(document_id, page=page, page_size=page_size)
    response = DocumentVersionListResponse(
        items=tuple(_version_response(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))


@router.get("/document-versions/{version_id}/download")
async def get_document_download(
    version_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> dict[str, object]:
    result = await DocumentService(
        session,
        actor,
        storage,
        request.app.state.settings,
    ).get_download_access(version_id)
    response = DocumentDownloadAccessResponse(url=result.url, expires_at=result.expires_at)
    return success_envelope(response.model_dump(mode="json"))


@router.get(
    "/document-versions/{version_id}/preview",
    response_model=None,
    responses={status.HTTP_202_ACCEPTED: {"description": "Preview conversion is queued"}},
)
async def get_document_preview(
    version_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
) -> dict[str, object] | JSONResponse:
    result = await DocumentService(
        session, actor, storage, request.app.state.settings
    ).get_preview_access(version_id)
    response = DocumentPreviewAccessResponse(
        status=result.status,
        preview_type=result.preview_type,
        url=result.url,
        expires_at=result.expires_at,
    )
    body = success_envelope(response.model_dump(mode="json"))
    if result.status == "QUEUED":
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=body)
    return body


@router.post(
    "/documents/{document_id}/versions",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document_version(
    document_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
    file: Annotated[UploadFile, File()],
    comment: Annotated[str | None, Form(max_length=10_000)] = None,
) -> dict[str, object]:
    result = await DocumentService(
        session,
        actor,
        storage,
        request.app.state.settings,
    ).add_version(
        document_id,
        DocumentVersionUpload(
            original_file_name=file.filename or "",
            content_type=file.content_type or "application/octet-stream",
            stream=file.file,
            comment=comment,
        ),
        audit=AuditContext(
            request_id=UUID(get_request_id()),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ),
    )
    response = DocumentUploadResponse(
        document_id=result.document_id,
        version_id=result.version_id,
        version_number=result.version_number,
        scan_status="PENDING",
    )
    return success_envelope(response.model_dump(mode="json"))
