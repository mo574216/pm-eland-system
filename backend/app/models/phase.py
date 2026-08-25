"""Workspace-scoped project phase and MVP deliverable associations."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Phase(Base):
    __tablename__ = "phases"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_phases_workspace_key"),
        UniqueConstraint("workspace_id", "sequence_number", name="uq_phases_workspace_sequence"),
        UniqueConstraint("id", "workspace_id", name="uq_phases_id_workspace"),
        CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'ARCHIVED')",
            name="ck_phases_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    sequence_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="PLANNED", server_default="PLANNED")
    is_locked: Mapped[bool] = mapped_column(default=False, server_default="false")
    locked_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class PhaseDeliverable(Base):
    __tablename__ = "phase_deliverables"
    __table_args__ = (
        CheckConstraint(
            "((entity_id IS NOT NULL)::integer + (document_id IS NOT NULL)::integer + "
            "(form_instance_id IS NOT NULL)::integer) = 1",
            name="ck_phase_deliverables_single_resource",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'SUBMITTED', 'APPROVED', 'REVISION_REQUESTED')",
            name="ck_phase_deliverables_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    phase_id: Mapped[UUID] = mapped_column(ForeignKey("phases.id", ondelete="CASCADE"))
    entity_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_objects.id", ondelete="CASCADE")
    )
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    form_instance_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("form_instances.id", ondelete="CASCADE")
    )
    is_required: Mapped[bool] = mapped_column(default=True, server_default="true")
    status: Mapped[str] = mapped_column(String(30), default="PENDING", server_default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
