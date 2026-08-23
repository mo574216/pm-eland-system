"""Create reusable import profiles, mappings, jobs, and conflicts.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | Sequence[str] | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column(
            "matching_strategy",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "configuration",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("source_type IN ('XLSX', 'CSV')", name="ck_import_profiles_source_type"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_import_profiles_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_type_id"],
            ["entity_types.id"],
            name="fk_import_profiles_entity_type_id_entity_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_import_profiles_created_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_profiles"),
    )
    op.create_table(
        "import_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_profile_id", sa.Uuid(), nullable=False),
        sa.Column("source_sheet", sa.String(length=255)),
        sa.Column("source_column", sa.String(length=255), nullable=False),
        sa.Column("target_attribute_definition_id", sa.Uuid()),
        sa.Column("target_system_field", sa.String(length=120)),
        sa.Column(
            "transformation_config",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint(
            "target_attribute_definition_id IS NOT NULL OR target_system_field IS NOT NULL",
            name="ck_import_mappings_target",
        ),
        sa.ForeignKeyConstraint(
            ["import_profile_id"],
            ["import_profiles.id"],
            name="fk_import_mappings_import_profile_id_import_profiles",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_attribute_definition_id"],
            ["attribute_definitions.id"],
            name="fk_import_mappings_attribute_definition",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_mappings"),
    )
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("import_profile_id", sa.Uuid()),
        sa.Column("source_object_key", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="UPLOADED", nullable=False),
        sa.Column("dry_run_summary", postgresql.JSONB()),
        sa.Column("final_summary", postgresql.JSONB()),
        sa.Column("requested_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.String(length=255)),
        sa.Column("error_message", sa.Text()),
        sa.CheckConstraint(
            "status IN ('UPLOADED', 'ANALYZING', 'READY_FOR_REVIEW', "
            "'VALIDATION_FAILED', 'READY_TO_COMMIT', 'COMMITTING', "
            "'COMPLETED', 'FAILED', 'CANCELLED')",
            name="ck_import_jobs_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_import_jobs_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["import_profile_id"],
            ["import_profiles.id"],
            name="fk_import_jobs_import_profile_id_import_profiles",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            name="fk_import_jobs_requested_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_jobs"),
    )
    op.create_index(
        "uq_import_jobs_idempotency",
        "import_jobs",
        ["workspace_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.create_table(
        "import_conflicts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_job_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer()),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column("attribute_key", sa.String(length=120)),
        sa.Column("existing_value", postgresql.JSONB()),
        sa.Column("imported_value", postgresql.JSONB()),
        sa.Column("resolution", sa.String(length=20)),
        sa.Column("resolved_by", sa.Uuid()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "resolution IS NULL OR resolution IN ('MERGE', 'REPLACE', 'SKIP')",
            name="ck_import_conflicts_resolution",
        ),
        sa.ForeignKeyConstraint(
            ["import_job_id"],
            ["import_jobs.id"],
            name="fk_import_conflicts_import_job_id_import_jobs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entity_objects.id"],
            name="fk_import_conflicts_entity_id_entity_objects",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"],
            ["users.id"],
            name="fk_import_conflicts_resolved_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_import_conflicts"),
    )
    op.create_index("idx_import_conflicts_job", "import_conflicts", ["import_job_id"])


def downgrade() -> None:
    op.drop_index("idx_import_conflicts_job", table_name="import_conflicts")
    op.drop_table("import_conflicts")
    op.drop_index("uq_import_jobs_idempotency", table_name="import_jobs")
    op.drop_table("import_jobs")
    op.drop_table("import_mappings")
    op.drop_table("import_profiles")
