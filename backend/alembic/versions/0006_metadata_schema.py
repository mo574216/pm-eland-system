"""Create generic entity-type and attribute-definition metadata schema.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

SUPPORTED_ATTRIBUTE_TYPES = (
    "TEXT",
    "RICH_TEXT",
    "INTEGER",
    "DECIMAL",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "ENUM",
    "MULTI_ENUM",
    "USER_REFERENCE",
    "ENTITY_REFERENCE",
    "FILE_REFERENCE",
    "JSON",
    "TABLE",
)

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entity_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("plural_name", sa.String(length=180)),
        sa.Column("description", sa.Text()),
        sa.Column("icon_key", sa.String(length=100)),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_entity_types_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_entity_types_created_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_entity_types"),
        sa.UniqueConstraint("workspace_id", "key", name="uq_entity_types_workspace_key"),
    )
    op.create_index("idx_entity_types_workspace", "entity_types", ["workspace_id"])
    op.create_index("idx_entity_types_active", "entity_types", ["workspace_id", "is_active"])

    allowed_types = ", ".join(f"'{value}'" for value in SUPPORTED_ATTRIBUTE_TYPES)
    op.create_table(
        "attribute_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("data_type", sa.String(length=40), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_read_only", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("default_value", postgresql.JSONB()),
        sa.Column(
            "validation_config",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "display_config",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "inheritance_config",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            f"data_type IN ({allowed_types})", name="ck_attribute_definitions_data_type"
        ),
        sa.ForeignKeyConstraint(
            ["entity_type_id"],
            ["entity_types.id"],
            name="fk_attribute_definitions_entity_type_id_entity_types",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attribute_definitions"),
        sa.UniqueConstraint("entity_type_id", "key", name="uq_attribute_definitions_type_key"),
    )
    op.create_index("idx_attribute_definitions_type", "attribute_definitions", ["entity_type_id"])
    op.create_index(
        "idx_attribute_definitions_active", "attribute_definitions", ["entity_type_id", "is_active"]
    )


def downgrade() -> None:
    op.drop_index("idx_attribute_definitions_active", table_name="attribute_definitions")
    op.drop_index("idx_attribute_definitions_type", table_name="attribute_definitions")
    op.drop_table("attribute_definitions")
    op.drop_index("idx_entity_types_active", table_name="entity_types")
    op.drop_index("idx_entity_types_workspace", table_name="entity_types")
    op.drop_table("entity_types")
