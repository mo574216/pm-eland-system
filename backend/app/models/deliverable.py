"""Generic governed deliverables and immutable submission evidence."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Deliverable(Base):
    __tablename__ = "deliverables"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_deliverables_workspace_key"),
        UniqueConstraint("id", "workspace_id", name="uq_deliverables_id_workspace"),
        ForeignKeyConstraint(
            ["phase_id", "workspace_id"],
            ["phases.id", "phases.workspace_id"],
            name="fk_deliverables_phase_workspace",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    phase_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    internal_reviewer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    internal_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    official_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requirements: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class DeliverableAssignment(Base):
    __tablename__ = "deliverable_assignments"
    __table_args__ = (
        UniqueConstraint(
            "deliverable_id", "user_id", "assignment_kind", name="uq_deliverable_assignment"
        ),
        ForeignKeyConstraint(
            ["deliverable_id", "workspace_id"],
            ["deliverables.id", "deliverables.workspace_id"],
            name="fk_deliverable_assignments_scope",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "assignment_kind IN ('OWNER', 'CONTRIBUTOR', 'INTERNAL_REVIEWER')",
            name="ck_deliverable_assignment_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    deliverable_id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    assignment_kind: Mapped[str] = mapped_column(String(40))
    assigned_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliverableVersion(Base):
    __tablename__ = "deliverable_versions"
    __table_args__ = (
        UniqueConstraint("deliverable_id", "version_number", name="uq_deliverable_versions_number"),
        UniqueConstraint("id", "workspace_id", name="uq_deliverable_versions_scope"),
        ForeignKeyConstraint(
            ["deliverable_id", "workspace_id"],
            ["deliverables.id", "deliverables.workspace_id"],
            name="fk_deliverable_versions_scope",
            ondelete="CASCADE",
        ),
        CheckConstraint("version_number > 0", name="ck_deliverable_version_positive"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    deliverable_id: Mapped[UUID]
    version_number: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)
    context_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliverablePackageItem(Base):
    __tablename__ = "deliverable_package_items"
    __table_args__ = (
        UniqueConstraint(
            "deliverable_version_id", "resource_kind", "resource_id", name="uq_package_item"
        ),
        ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_package_items_version_scope",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "resource_kind IN ('ENTITY', 'DOCUMENT_VERSION', 'FORM_INSTANCE')",
            name="ck_package_item_resource_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    deliverable_version_id: Mapped[UUID]
    resource_kind: Mapped[str] = mapped_column(String(40))
    resource_id: Mapped[UUID]
    resource_version: Mapped[int | None] = mapped_column(Integer)
    label_snapshot: Mapped[str] = mapped_column(String(500))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    metadata_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("deliverable_id", "sequence_number", name="uq_submissions_sequence"),
        UniqueConstraint("id", "workspace_id", name="uq_submissions_scope"),
        UniqueConstraint("deliverable_id", "idempotency_key", name="uq_submissions_idempotency"),
        ForeignKeyConstraint(
            ["deliverable_id", "workspace_id"],
            ["deliverables.id", "deliverables.workspace_id"],
            name="fk_submissions_deliverable_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_submissions_version_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["prior_submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_submissions_prior_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint("sequence_number > 0", name="ck_submission_sequence_positive"),
        CheckConstraint(
            "submission_kind IN ('SUBMISSION', 'RESUBMISSION')", name="ck_submission_kind"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    deliverable_id: Mapped[UUID]
    deliverable_version_id: Mapped[UUID]
    sequence_number: Mapped[int] = mapped_column(Integer)
    submission_kind: Mapped[str] = mapped_column(String(30))
    prior_submission_id: Mapped[UUID | None]
    submitter_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    statement: Mapped[str] = mapped_column(Text)
    related_comment_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    context_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    idempotency_key: Mapped[str] = mapped_column(String(255))
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SubmissionRecipient(Base):
    __tablename__ = "submission_recipients"
    __table_args__ = (
        UniqueConstraint("submission_id", "user_id", name="uq_submission_recipient"),
        ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_submission_recipients_scope",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    submission_id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubmissionWithdrawal(Base):
    __tablename__ = "submission_withdrawals"
    __table_args__ = (
        UniqueConstraint(
            "submission_id", "idempotency_key", name="uq_submission_withdrawals_idempotency"
        ),
        ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_submission_withdrawals_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    submission_id: Mapped[UUID]
    withdrawn_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reason: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    withdrawn_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
