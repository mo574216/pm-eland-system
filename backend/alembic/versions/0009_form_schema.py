"""Create metadata-driven form definitions, fields, and instances.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "form_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type_id", sa.Uuid()),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "lifecycle_status",
            sa.String(length=30),
            server_default="DRAFT",
            nullable=False,
        ),
        sa.Column(
            "schema_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("retired_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("version_number > 0", name="ck_form_definitions_version_positive"),
        sa.CheckConstraint(
            "lifecycle_status IN ('DRAFT', 'PUBLISHED', 'RETIRED')",
            name="ck_form_definitions_lifecycle_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_form_definitions_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_type_id"],
            ["entity_types.id"],
            name="fk_form_definitions_entity_type_id_entity_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_form_definitions_created_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_form_definitions"),
        sa.UniqueConstraint(
            "workspace_id",
            "key",
            "version_number",
            name="uq_form_definitions_workspace_key_version",
        ),
    )
    op.create_index(
        "idx_form_definitions_workspace_status",
        "form_definitions",
        ["workspace_id", "lifecycle_status"],
    )
    op.create_index(
        "idx_form_definitions_entity_type",
        "form_definitions",
        ["entity_type_id"],
    )

    op.create_table(
        "form_fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("form_definition_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_definition_id", sa.Uuid()),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=180), nullable=False),
        sa.Column("field_type", sa.String(length=40), nullable=False),
        sa.Column("section_key", sa.String(length=120)),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_read_only", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "visibility_rule",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "validation_rule",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "inheritance_rule",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["form_definition_id"],
            ["form_definitions.id"],
            name="fk_form_fields_form_definition_id_form_definitions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_definition_id"],
            ["attribute_definitions.id"],
            name="fk_form_fields_attribute_definition_id_attribute_definitions",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_form_fields"),
        sa.UniqueConstraint(
            "form_definition_id",
            "key",
            name="uq_form_fields_definition_key",
        ),
    )
    op.create_index(
        "idx_form_fields_definition_order",
        "form_fields",
        ["form_definition_id", "display_order"],
    )

    op.create_table(
        "form_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("form_definition_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="DRAFT", nullable=False),
        sa.Column(
            "values_json",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("submitted_by", sa.Uuid()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REVISION_REQUESTED')",
            name="ck_form_instances_status",
        ),
        sa.CheckConstraint("version > 0", name="ck_form_instances_version_positive"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_form_instances_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["form_definition_id"],
            ["form_definitions.id"],
            name="fk_form_instances_form_definition_id_form_definitions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entity_objects.id"],
            name="fk_form_instances_entity_id_entity_objects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by"],
            ["users.id"],
            name="fk_form_instances_submitted_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_form_instances"),
    )
    op.create_index("idx_form_instances_workspace", "form_instances", ["workspace_id"])
    op.create_index("idx_form_instances_entity", "form_instances", ["entity_id"])
    op.create_index("idx_form_instances_form", "form_instances", ["form_definition_id"])
    op.create_index(
        "idx_form_instances_values_gin",
        "form_instances",
        ["values_json"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_form_instances_values_gin", table_name="form_instances")
    op.drop_index("idx_form_instances_form", table_name="form_instances")
    op.drop_index("idx_form_instances_entity", table_name="form_instances")
    op.drop_index("idx_form_instances_workspace", table_name="form_instances")
    op.drop_table("form_instances")
    op.drop_index("idx_form_fields_definition_order", table_name="form_fields")
    op.drop_table("form_fields")
    op.drop_index("idx_form_definitions_entity_type", table_name="form_definitions")
    op.drop_index("idx_form_definitions_workspace_status", table_name="form_definitions")
    op.drop_table("form_definitions")
