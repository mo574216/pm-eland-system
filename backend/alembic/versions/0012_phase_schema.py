"""Create workspace phases and MVP phase-deliverable associations.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | Sequence[str] | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "phases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="PLANNED", nullable=False),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("locked_by", sa.Uuid()),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "status IN ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'ARCHIVED')", name="ck_phases_status"
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_phases_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["locked_by"], ["users.id"], name="fk_phases_locked_by_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_phases"),
        sa.UniqueConstraint("workspace_id", "key", name="uq_phases_workspace_key"),
        sa.UniqueConstraint("workspace_id", "sequence_number", name="uq_phases_workspace_sequence"),
    )
    op.create_index("idx_phases_workspace_status", "phases", ["workspace_id", "status"])
    op.create_table(
        "phase_deliverables",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("phase_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column("document_id", sa.Uuid()),
        sa.Column("form_instance_id", sa.Uuid()),
        sa.Column("is_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="PENDING", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "((entity_id IS NOT NULL)::integer + "
            "(document_id IS NOT NULL)::integer + "
            "(form_instance_id IS NOT NULL)::integer) = 1",
            name="ck_phase_deliverables_single_resource",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'SUBMITTED', 'APPROVED', 'REVISION_REQUESTED')",
            name="ck_phase_deliverables_status",
        ),
        sa.ForeignKeyConstraint(
            ["phase_id"],
            ["phases.id"],
            name="fk_phase_deliverables_phase_id_phases",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entity_objects.id"],
            name="fk_phase_deliverables_entity_id_entity_objects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name="fk_phase_deliverables_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["form_instance_id"],
            ["form_instances.id"],
            name="fk_phase_deliverables_form_instance_id_form_instances",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_phase_deliverables"),
    )
    op.create_index("idx_phase_deliverables_phase", "phase_deliverables", ["phase_id"])


def downgrade() -> None:
    op.drop_index("idx_phase_deliverables_phase", table_name="phase_deliverables")
    op.drop_table("phase_deliverables")
    op.drop_index("idx_phases_workspace_status", table_name="phases")
    op.drop_table("phases")
