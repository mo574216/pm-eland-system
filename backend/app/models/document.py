"""Logical documents and immutable object-storage version metadata."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN ('ACTIVE', 'ARCHIVED', 'DELETED')",
            name="ck_documents_lifecycle_status",
        ),
        Index("idx_documents_workspace_entity", "workspace_id", "entity_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    entity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_objects.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    document_type: Mapped[str | None] = mapped_column(String(100))
    lifecycle_status: Mapped[str] = mapped_column(
        String(30), default="ACTIVE", server_default="ACTIVE"
    )
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "document_versions.id",
            name="fk_documents_current_version",
            ondelete="SET NULL",
            use_alter=True,
        )
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
        CheckConstraint("version_number > 0", name="ck_document_versions_number_positive"),
        CheckConstraint("file_size_bytes >= 0", name="ck_document_versions_file_size"),
        CheckConstraint(
            "scan_status IN ('PENDING', 'CLEAN', 'INFECTED', 'FAILED')",
            name="ck_document_versions_scan_status",
        ),
        CheckConstraint(
            "preview_status IN ('NOT_REQUESTED', 'QUEUED', 'READY', 'FAILED')",
            name="ck_document_versions_preview_status",
        ),
        Index("idx_document_versions_document", "document_id", text("version_number DESC")),
        Index("uq_document_object_key", "object_key", unique=True),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(Text)
    original_file_name: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(255))
    file_extension: Mapped[str | None] = mapped_column(String(50))
    file_size_bytes: Mapped[int] = mapped_column()
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    storage_provider: Mapped[str] = mapped_column(
        String(30), default="MINIO", server_default="MINIO"
    )
    scan_status: Mapped[str] = mapped_column(
        String(30), default="PENDING", server_default="PENDING"
    )
    preview_status: Mapped[str] = mapped_column(
        String(30), default="NOT_REQUESTED", server_default="NOT_REQUESTED"
    )
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    comment: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
