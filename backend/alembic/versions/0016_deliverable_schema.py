"""Create governed deliverable and immutable submission persistence.

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_phases_id_workspace", "phases", ["id", "workspace_id"])
    op.create_table(
        "deliverables",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("phase_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("owner_id", sa.Uuid()),
        sa.Column("internal_reviewer_id", sa.Uuid()),
        sa.Column("internal_due_at", sa.DateTime(timezone=True)),
        sa.Column("official_due_at", sa.DateTime(timezone=True)),
        sa.Column(
            "requirements",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(
            ["phase_id", "workspace_id"],
            ["phases.id", "phases.workspace_id"],
            name="fk_deliverables_phase_workspace",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["internal_reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "key", name="uq_deliverables_workspace_key"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_deliverables_id_workspace"),
    )
    op.create_index("idx_deliverables_phase", "deliverables", ["workspace_id", "phase_id"])

    op.create_table(
        "deliverable_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_kind", sa.String(40), nullable=False),
        sa.Column("assigned_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "assignment_kind IN ('OWNER', 'CONTRIBUTOR', 'INTERNAL_REVIEWER')",
            name="ck_deliverable_assignment_kind",
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_id", "workspace_id"],
            ["deliverables.id", "deliverables.workspace_id"],
            name="fk_deliverable_assignments_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "deliverable_id", "user_id", "assignment_kind", name="uq_deliverable_assignment"
        ),
    )
    op.create_index(
        "idx_deliverable_assignments_user", "deliverable_assignments", ["workspace_id", "user_id"]
    )

    op.create_table(
        "deliverable_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column(
            "context_snapshot",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("version_number > 0", name="ck_deliverable_version_positive"),
        sa.ForeignKeyConstraint(
            ["deliverable_id", "workspace_id"],
            ["deliverables.id", "deliverables.workspace_id"],
            name="fk_deliverable_versions_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "deliverable_id", "version_number", name="uq_deliverable_versions_number"
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_deliverable_versions_scope"),
    )

    op.create_table(
        "deliverable_package_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_version_id", sa.Uuid(), nullable=False),
        sa.Column("resource_kind", sa.String(40), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("resource_version", sa.Integer()),
        sa.Column("label_snapshot", sa.String(500), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "metadata_snapshot",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "resource_kind IN ('ENTITY', 'DOCUMENT_VERSION', 'FORM_INSTANCE')",
            name="ck_package_item_resource_kind",
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_package_items_version_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "deliverable_version_id", "resource_kind", "resource_id", name="uq_package_item"
        ),
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_version_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("submission_kind", sa.String(30), nullable=False),
        sa.Column("prior_submission_id", sa.Uuid()),
        sa.Column("submitter_id", sa.Uuid()),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column(
            "related_comment_ids",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "context_snapshot",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("sequence_number > 0", name="ck_submission_sequence_positive"),
        sa.CheckConstraint(
            "submission_kind IN ('SUBMISSION', 'RESUBMISSION')", name="ck_submission_kind"
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_id", "workspace_id"],
            ["deliverables.id", "deliverables.workspace_id"],
            name="fk_submissions_deliverable_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_submissions_version_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["prior_submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_submissions_prior_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["submitter_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deliverable_id", "sequence_number", name="uq_submissions_sequence"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_submissions_scope"),
        sa.UniqueConstraint("deliverable_id", "idempotency_key", name="uq_submissions_idempotency"),
    )
    op.create_index(
        "idx_submissions_deliverable",
        "submissions",
        ["workspace_id", "deliverable_id", "sequence_number"],
    )

    op.create_table(
        "submission_recipients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_submission_recipients_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id", "user_id", name="uq_submission_recipient"),
    )

    op.create_table(
        "submission_withdrawals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("withdrawn_by", sa.Uuid()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "withdrawn_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_submission_withdrawals_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["withdrawn_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "submission_id", "idempotency_key", name="uq_submission_withdrawals_idempotency"
        ),
    )


def downgrade() -> None:
    op.drop_table("submission_withdrawals")
    op.drop_table("submission_recipients")
    op.drop_index("idx_submissions_deliverable", table_name="submissions")
    op.drop_table("submissions")
    op.drop_table("deliverable_package_items")
    op.drop_table("deliverable_versions")
    op.drop_index("idx_deliverable_assignments_user", table_name="deliverable_assignments")
    op.drop_table("deliverable_assignments")
    op.drop_index("idx_deliverables_phase", table_name="deliverables")
    op.drop_table("deliverables")
    op.drop_constraint("uq_phases_id_workspace", "phases", type_="unique")
