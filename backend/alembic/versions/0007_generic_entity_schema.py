"""Create canonical generic entity-object schema.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entity_objects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid()),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=40), server_default="ACTIVE", nullable=False),
        sa.Column(
            "attributes",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid()),
        sa.Column("updated_by", sa.Uuid()),
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
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'ARCHIVED', 'DELETED')",
            name="ck_entity_objects_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_entity_objects_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_type_id"],
            ["entity_types.id"],
            name="fk_entity_objects_entity_type_id_entity_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["entity_objects.id"],
            name="fk_entity_objects_parent_id_entity_objects",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_entity_objects_created_by_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
            name="fk_entity_objects_updated_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_entity_objects"),
    )
    active_rows = sa.text("deleted_at IS NULL")
    op.create_index(
        "idx_entity_objects_workspace",
        "entity_objects",
        ["workspace_id"],
        postgresql_where=active_rows,
    )
    op.create_index(
        "idx_entity_objects_type",
        "entity_objects",
        ["workspace_id", "entity_type_id"],
        postgresql_where=active_rows,
    )
    op.create_index(
        "idx_entity_objects_parent",
        "entity_objects",
        ["parent_id"],
        postgresql_where=active_rows,
    )
    op.create_index("idx_entity_objects_name", "entity_objects", ["workspace_id", "name"])
    op.create_index(
        "idx_entity_objects_attributes_gin",
        "entity_objects",
        ["attributes"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_entity_objects_attributes_gin", table_name="entity_objects")
    op.drop_index("idx_entity_objects_name", table_name="entity_objects")
    op.drop_index("idx_entity_objects_parent", table_name="entity_objects")
    op.drop_index("idx_entity_objects_type", table_name="entity_objects")
    op.drop_index("idx_entity_objects_workspace", table_name="entity_objects")
    op.drop_table("entity_objects")
