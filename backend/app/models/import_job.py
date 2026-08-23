"""Reusable metadata-driven import profiles, jobs, mappings, and conflicts."""

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
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportProfile(Base):
    __tablename__ = "import_profiles"
    __table_args__ = (
        CheckConstraint("source_type IN ('XLSX', 'CSV')", name="ck_import_profiles_source_type"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    entity_type_id: Mapped[UUID] = mapped_column(ForeignKey("entity_types.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(20))
    matching_strategy: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImportMapping(Base):
    __tablename__ = "import_mappings"
    __table_args__ = (
        CheckConstraint(
            "target_attribute_definition_id IS NOT NULL OR target_system_field IS NOT NULL",
            name="ck_import_mappings_target",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("import_profiles.id", ondelete="CASCADE")
    )
    source_sheet: Mapped[str | None] = mapped_column(String(255))
    source_column: Mapped[str] = mapped_column(String(255))
    target_attribute_definition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attribute_definitions.id", ondelete="RESTRICT")
    )
    target_system_field: Mapped[str | None] = mapped_column(String(120))
    transformation_config: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('UPLOADED', 'ANALYZING', 'READY_FOR_REVIEW', "
            "'VALIDATION_FAILED', 'READY_TO_COMMIT', 'COMMITTING', "
            "'COMPLETED', 'FAILED', 'CANCELLED')",
            name="ck_import_jobs_status",
        ),
        Index(
            "uq_import_jobs_idempotency",
            "workspace_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    import_profile_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("import_profiles.id", ondelete="SET NULL")
    )
    source_object_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="UPLOADED", server_default="UPLOADED")
    dry_run_summary: Mapped[dict[str, object] | None] = mapped_column(JSONB())
    final_summary: Mapped[dict[str, object] | None] = mapped_column(JSONB())
    requested_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)


class ImportConflict(Base):
    __tablename__ = "import_conflicts"
    __table_args__ = (
        CheckConstraint(
            "resolution IS NULL OR resolution IN ('MERGE', 'REPLACE', 'SKIP')",
            name="ck_import_conflicts_resolution",
        ),
        Index("idx_import_conflicts_job", "import_job_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    import_job_id: Mapped[UUID] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"))
    row_number: Mapped[int | None] = mapped_column(Integer)
    entity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_objects.id", ondelete="SET NULL")
    )
    attribute_key: Mapped[str | None] = mapped_column(String(120))
    existing_value: Mapped[object | None] = mapped_column(JSONB())
    imported_value: Mapped[object | None] = mapped_column(JSONB())
    resolution: Mapped[str | None] = mapped_column(String(20))
    resolved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
