"""Document upload API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    version_id: UUID
    version_number: int = Field(ge=1)
    scan_status: Literal["PENDING"]


class DocumentDownloadAccessResponse(BaseModel):
    url: str
    expires_at: datetime


class DocumentPreviewAccessResponse(BaseModel):
    status: Literal["NOT_REQUESTED", "QUEUED", "READY", "FAILED"]
    preview_type: Literal["PDF", "IMAGE"] | None
    url: str | None
    expires_at: datetime | None


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    original_file_name: str
    content_type: str | None
    file_extension: str | None
    file_size_bytes: int
    checksum_sha256: str | None
    scan_status: Literal["PENDING", "CLEAN", "INFECTED", "FAILED"]
    preview_status: Literal["NOT_REQUESTED", "QUEUED", "READY", "FAILED"]
    uploaded_by: UUID | None
    uploaded_at: datetime
    comment: str | None
    metadata: dict[str, object]


class DocumentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    entity_id: UUID | None
    title: str
    description: str | None
    document_type: str | None
    lifecycle_status: Literal["ACTIVE", "ARCHIVED", "DELETED"]
    current_version_id: UUID | None
    current_version: DocumentVersionResponse | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: tuple[DocumentResponse, ...]
    page: int
    page_size: int
    total: int


class DocumentVersionListResponse(BaseModel):
    items: tuple[DocumentVersionResponse, ...]
    page: int
    page_size: int
    total: int
