"""Immutable phase acceptance evidence and governed condition projections."""

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


class AcceptancePackage(Base):
    __tablename__ = "acceptance_packages"
    __table_args__ = (
        UniqueConstraint("id", "workspace_id", name="uq_acceptance_packages_scope"),
        UniqueConstraint("phase_id", "sequence_number", name="uq_acceptance_packages_sequence"),
        UniqueConstraint("phase_id", "idempotency_key", name="uq_acceptance_packages_idempotency"),
        ForeignKeyConstraint(
            ["phase_id", "workspace_id"],
            ["phases.id", "phases.workspace_id"],
            name="fk_acceptance_packages_phase_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    phase_id: Mapped[UUID]
    sequence_number: Mapped[int] = mapped_column(Integer)
    statement: Mapped[str] = mapped_column(Text)
    employer_recipient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    requested_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    evidence_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    idempotency_key: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AcceptancePackageItem(Base):
    __tablename__ = "acceptance_package_items"
    __table_args__ = (
        UniqueConstraint("acceptance_package_id", "submission_id", name="uq_acceptance_item"),
        ForeignKeyConstraint(
            ["acceptance_package_id", "workspace_id"],
            ["acceptance_packages.id", "acceptance_packages.workspace_id"],
            name="fk_acceptance_items_package_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_acceptance_items_submission_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_acceptance_items_version_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    acceptance_package_id: Mapped[UUID]
    submission_id: Mapped[UUID]
    deliverable_version_id: Mapped[UUID]
    review_outcome_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    label_snapshot: Mapped[str] = mapped_column(String(500))


class AcceptanceDecision(Base):
    __tablename__ = "acceptance_decisions"
    __table_args__ = (
        UniqueConstraint("id", "workspace_id", name="uq_acceptance_decisions_scope"),
        UniqueConstraint("acceptance_package_id", name="uq_acceptance_decisions_package"),
        UniqueConstraint(
            "acceptance_package_id", "idempotency_key", name="uq_acceptance_decisions_idempotency"
        ),
        ForeignKeyConstraint(
            ["acceptance_package_id", "workspace_id"],
            ["acceptance_packages.id", "acceptance_packages.workspace_id"],
            name="fk_acceptance_decisions_package_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "decision_kind IN ('ACCEPT', 'CONDITIONAL_ACCEPT', 'REJECT')",
            name="ck_acceptance_decisions_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    acceptance_package_id: Mapped[UUID]
    decision_kind: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    authority_kind: Mapped[str] = mapped_column(
        String(40), default="EMPLOYER_ACCEPTANCE", server_default="EMPLOYER_ACCEPTANCE"
    )
    statement: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AcceptanceCondition(Base):
    __tablename__ = "acceptance_conditions"
    __table_args__ = (
        UniqueConstraint("id", "workspace_id", name="uq_acceptance_conditions_scope"),
        ForeignKeyConstraint(
            ["decision_id", "workspace_id"],
            ["acceptance_decisions.id", "acceptance_decisions.workspace_id"],
            name="fk_acceptance_conditions_decision_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'SUBMITTED_FOR_VERIFICATION', "
            "'SATISFIED', 'OVERDUE', 'REJECTED')",
            name="ck_acceptance_conditions_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    decision_id: Mapped[UUID]
    description: Mapped[str] = mapped_column(Text)
    responsible_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    verifier_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    due_at: Mapped[datetime]
    evidence_requirement: Mapped[str] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    status: Mapped[str] = mapped_column(String(40), default="OPEN", server_default="OPEN")
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AcceptanceConditionEvent(Base):
    __tablename__ = "acceptance_condition_events"
    __table_args__ = (
        UniqueConstraint("condition_id", "idempotency_key", name="uq_condition_events_idempotency"),
        ForeignKeyConstraint(
            ["condition_id", "workspace_id"],
            ["acceptance_conditions.id", "acceptance_conditions.workspace_id"],
            name="fk_condition_events_condition_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "action_kind IN ('SUBMIT_EVIDENCE', 'VERIFY', 'REJECT_EVIDENCE')",
            name="ck_condition_events_action",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    condition_id: Mapped[UUID]
    action_kind: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    previous_status: Mapped[str] = mapped_column(String(40))
    resulting_status: Mapped[str] = mapped_column(String(40))
    statement: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    resulting_version: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AcceptanceClosure(Base):
    __tablename__ = "acceptance_closures"
    __table_args__ = (
        UniqueConstraint("decision_id", name="uq_acceptance_closures_decision"),
        UniqueConstraint(
            "decision_id", "idempotency_key", name="uq_acceptance_closures_idempotency"
        ),
        ForeignKeyConstraint(
            ["decision_id", "workspace_id"],
            ["acceptance_decisions.id", "acceptance_decisions.workspace_id"],
            name="fk_acceptance_closures_decision_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    decision_id: Mapped[UUID]
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    statement: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
