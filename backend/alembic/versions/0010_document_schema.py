"""Create logical documents and immutable document versions.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("document_type", sa.String(length=100)),
        sa.Column(
            "lifecycle_status", sa.String(length=30), server_default="ACTIVE", nullable=False
        ),
        sa.Column("current_version_id", sa.Uuid()),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "lifecycle_status IN ('ACTIVE', 'ARCHIVED', 'DELETED')",
            name="ck_documents_lifecycle_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_documents_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entity_objects.id"],
            name="fk_documents_entity_id_entity_objects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name="fk_documents_created_by_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
    )
    op.create_index("idx_documents_workspace_entity", "documents", ["workspace_id", "entity_id"])

    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("original_file_name", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=255)),
        sa.Column("file_extension", sa.String(length=50)),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64)),
        sa.Column("storage_provider", sa.String(length=30), server_default="MINIO", nullable=False),
        sa.Column("scan_status", sa.String(length=30), server_default="PENDING", nullable=False),
        sa.Column(
            "preview_status", sa.String(length=30), server_default="NOT_REQUESTED", nullable=False
        ),
        sa.Column("uploaded_by", sa.Uuid()),
        sa.Column(
            "uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("comment", sa.Text()),
        sa.Column(
            "metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.CheckConstraint("version_number > 0", name="ck_document_versions_number_positive"),
        sa.CheckConstraint("file_size_bytes >= 0", name="ck_document_versions_file_size"),
        sa.CheckConstraint(
            "scan_status IN ('PENDING', 'CLEAN', 'INFECTED', 'FAILED')",
            name="ck_document_versions_scan_status",
        ),
        sa.CheckConstraint(
            "preview_status IN ('NOT_REQUESTED', 'QUEUED', 'READY', 'FAILED')",
            name="ck_document_versions_preview_status",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_document_versions_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
            name="fk_document_versions_uploaded_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_versions"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
    )
    op.create_index(
        "idx_document_versions_document",
        "document_versions",
        ["document_id", sa.text("version_number DESC")],
    )
    op.create_index("uq_document_object_key", "document_versions", ["object_key"], unique=True)
    op.create_foreign_key(
        "fk_documents_current_version",
        "documents",
        "document_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_documents_current_version", "documents", type_="foreignkey")
    op.drop_index("uq_document_object_key", table_name="document_versions")
    op.drop_index("idx_document_versions_document", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index("idx_documents_workspace_entity", table_name="documents")
    op.drop_table("documents")
