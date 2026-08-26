"""Add immutable version-bound review evidence and revision transitions.

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-26
"""

# ruff: noqa: E501 -- SQL remains line-oriented so migration statements are auditable.

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_comments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_version_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid()),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="OPEN", nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("id", "workspace_id", name="uq_review_comments_scope"),
        sa.UniqueConstraint(
            "submission_id", "idempotency_key", name="uq_review_comments_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_review_comments_submission_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_review_comments_version_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('OPEN')", name="ck_review_comments_status"),
    )
    op.create_table(
        "review_outcomes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_version_id", sa.Uuid(), nullable=False),
        sa.Column("outcome_kind", sa.String(50), nullable=False),
        sa.Column("authority_kind", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("related_comment_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "submission_id", "idempotency_key", name="uq_review_outcomes_idempotency"
        ),
        sa.ForeignKeyConstraint(
            ["submission_id", "workspace_id"],
            ["submissions.id", "submissions.workspace_id"],
            name="fk_review_outcomes_submission_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["deliverable_version_id", "workspace_id"],
            ["deliverable_versions.id", "deliverable_versions.workspace_id"],
            name="fk_review_outcomes_version_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "outcome_kind IN ('CLARIFICATION', 'REVISION_REQUEST', 'RECOMMENDATION', 'CONDITIONAL_RECOMMENDATION', 'REJECTION_MAJOR_REVISION', 'TECHNICAL_SIGN_OFF')",
            name="ck_review_outcomes_kind",
        ),
        sa.CheckConstraint(
            "authority_kind IN ('PROJECT_REVIEW', 'TECHNICAL_REVIEW')",
            name="ck_review_outcomes_authority",
        ),
    )
    op.execute(
        sa.text("""
        INSERT INTO workflow_transition_definitions
            (id, workspace_id, definition_version_id, key, label, from_state_id,
             to_state_id, required_permission, authority_kind, assignment_kind,
             reason_required, policy)
        SELECT gen_random_uuid(), wv.workspace_id, wv.id, item.key, item.label,
               source.id, target.id, item.permission, item.authority,
               'REVIEW_RECIPIENT', true,
               jsonb_build_object('requires_review_outcome', true)
        FROM workflow_definition_versions wv
        JOIN workflow_definitions wd ON wd.id = wv.definition_id
        CROSS JOIN (VALUES
            ('project_request_revision', 'درخواست اصلاح توسط مدیر پروژه', 'PROJECT_REVIEW', 'PROJECT_REVIEW'),
            ('technical_request_revision', 'درخواست اصلاح فنی', 'TECHNICAL_REVIEW', 'TECHNICAL_REVIEW')
        ) AS item(key, label, permission, authority)
        JOIN workflow_state_definitions source ON source.definition_version_id = wv.id AND source.key = 'submitted'
        JOIN workflow_state_definitions target ON target.definition_version_id = wv.id AND target.key = 'preparation'
        WHERE wd.key = 'system_deliverable_lifecycle'
          AND NOT EXISTS (SELECT 1 FROM workflow_transition_definitions wt WHERE wt.definition_version_id = wv.id AND wt.key = item.key)
    """)
    )
    op.execute(
        sa.text("""
        INSERT INTO workflow_assignments
            (id, workspace_id, instance_id, user_id, assignment_kind, assigned_by)
        SELECT gen_random_uuid(), sr.workspace_id, wi.id, sr.user_id,
               'REVIEW_RECIPIENT', s.submitter_id
        FROM submission_recipients sr
        JOIN submissions s ON s.id = sr.submission_id
        JOIN workflow_instances wi ON wi.target_kind = 'DELIVERABLE' AND wi.target_id = s.deliverable_id AND wi.workspace_id = s.workspace_id
        WHERE NOT EXISTS (SELECT 1 FROM workflow_assignments wa WHERE wa.instance_id = wi.id AND wa.user_id = sr.user_id AND wa.assignment_kind = 'REVIEW_RECIPIENT')
    """)
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM workflow_assignments wa
            USING workflow_instances wi, workflow_definition_versions wv,
                  workflow_definitions wd
            WHERE wa.instance_id = wi.id
              AND wi.definition_version_id = wv.id
              AND wv.definition_id = wd.id
              AND wd.key = 'system_deliverable_lifecycle'
              AND wa.assignment_kind = 'REVIEW_RECIPIENT'
            """
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM workflow_transition_definitions WHERE key IN ('project_request_revision', 'technical_request_revision')"
        )
    )
    op.drop_table("review_outcomes")
    op.drop_table("review_comments")
