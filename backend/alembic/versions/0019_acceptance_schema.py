"""Add immutable phase acceptance packages, decisions, conditions, and closure.

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "acceptance_packages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("phase_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("employer_recipient_id", sa.Uuid()),
        sa.Column("requested_by", sa.Uuid()),
        sa.Column("evidence_snapshot", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_acceptance_packages_scope"),
        sa.UniqueConstraint("phase_id", "sequence_number", name="uq_acceptance_packages_sequence"),
        sa.UniqueConstraint(
            "phase_id", "idempotency_key", name="uq_acceptance_packages_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["phase_id", "workspace_id"],
            ["phases.id", "phases.workspace_id"],
            name="fk_acceptance_packages_phase_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["employer_recipient_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "acceptance_package_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("acceptance_package_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_version_id", sa.Uuid(), nullable=False),
        sa.Column("review_outcome_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("label_snapshot", sa.String(500), nullable=False),
        sa.UniqueConstraint("acceptance_package_id", "submission_id", name="uq_acceptance_item"),
        sa.ForeignKeyConstraint(
            ["acceptance_package_id", "workspace_id"],
            ["acceptance_packages.id", "acceptance_packages.workspace_id"],
            name="fk_acceptance_items_package_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_acceptance_items_submission_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_acceptance_items_version_scope",
            ondelete="RESTRICT",
        ),
    )
    op.create_table(
        "acceptance_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("acceptance_package_id", sa.Uuid(), nullable=False),
        sa.Column("decision_kind", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column(
            "authority_kind", sa.String(40), server_default="EMPLOYER_ACCEPTANCE", nullable=False
        ),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_acceptance_decisions_scope"),
        sa.UniqueConstraint("acceptance_package_id", name="uq_acceptance_decisions_package"),
        sa.UniqueConstraint(
            "acceptance_package_id", "idempotency_key", name="uq_acceptance_decisions_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["acceptance_package_id", "workspace_id"],
            ["acceptance_packages.id", "acceptance_packages.workspace_id"],
            name="fk_acceptance_decisions_package_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "decision_kind IN ('ACCEPT', 'CONDITIONAL_ACCEPT', 'REJECT')",
            name="ck_acceptance_decisions_kind",
        ),
    )
    op.create_table(
        "acceptance_conditions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("responsible_id", sa.Uuid()),
        sa.Column("verifier_id", sa.Uuid()),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_requirement", sa.Text(), nullable=False),
        sa.Column("mandatory", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("status", sa.String(40), server_default="OPEN", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_acceptance_conditions_scope"),
        sa.ForeignKeyConstraint(
            ["decision_id", "workspace_id"],
            ["acceptance_decisions.id", "acceptance_decisions.workspace_id"],
            name="fk_acceptance_conditions_decision_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["responsible_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verifier_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'SUBMITTED_FOR_VERIFICATION', "
            "'SATISFIED', 'OVERDUE', 'REJECTED')",
            name="ck_acceptance_conditions_status",
        ),
    )
    op.create_table(
        "acceptance_condition_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("condition_id", sa.Uuid(), nullable=False),
        sa.Column("action_kind", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("previous_status", sa.String(40), nullable=False),
        sa.Column("resulting_status", sa.String(40), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("resulting_version", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "condition_id", "idempotency_key", name="uq_condition_events_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["condition_id", "workspace_id"],
            ["acceptance_conditions.id", "acceptance_conditions.workspace_id"],
            name="fk_condition_events_condition_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "action_kind IN ('SUBMIT_EVIDENCE', 'VERIFY', 'REJECT_EVIDENCE')",
            name="ck_condition_events_action",
        ),
    )
    op.create_table(
        "acceptance_closures",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "closed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("decision_id", name="uq_acceptance_closures_decision"),
        sa.UniqueConstraint(
            "decision_id", "idempotency_key", name="uq_acceptance_closures_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["decision_id", "workspace_id"],
            ["acceptance_decisions.id", "acceptance_decisions.workspace_id"],
            name="fk_acceptance_closures_decision_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("acceptance_closures")
    op.drop_table("acceptance_condition_events")
    op.drop_table("acceptance_conditions")
    op.drop_table("acceptance_decisions")
    op.drop_table("acceptance_package_items")
    op.drop_table("acceptance_packages")
