"""Create generic relationship-type and entity-relationship schema.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "relationship_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "directionality",
            sa.String(length=20),
            server_default="DIRECTED",
            nullable=False,
        ),
        sa.Column("source_type_id", sa.Uuid()),
        sa.Column("target_type_id", sa.Uuid()),
        sa.Column(
            "configuration",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "directionality IN ('DIRECTED', 'UNDIRECTED')",
            name="ck_relationship_types_directionality",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_relationship_types_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_type_id"],
            ["entity_types.id"],
            name="fk_relationship_types_source_type_id_entity_types",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_type_id"],
            ["entity_types.id"],
            name="fk_relationship_types_target_type_id_entity_types",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_relationship_types"),
        sa.UniqueConstraint(
            "workspace_id",
            "key",
            name="uq_relationship_types_workspace_key",
        ),
    )
    op.create_index(
        "idx_relationship_types_workspace_active",
        "relationship_types",
        ["workspace_id", "is_active"],
    )

    op.create_table(
        "entity_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type_id", sa.Uuid(), nullable=False),
        sa.Column("source_entity_id", sa.Uuid(), nullable=False),
        sa.Column("target_entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "attributes",
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
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "source_entity_id <> target_entity_id",
            name="ck_entity_relationships_distinct_entities",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_entity_relationships_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["relationship_type_id"],
            ["relationship_types.id"],
            name="fk_entity_relationships_relationship_type_id_relationship_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_entity_id"],
            ["entity_objects.id"],
            name="fk_entity_relationships_source_entity_id_entity_objects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_entity_id"],
            ["entity_objects.id"],
            name="fk_entity_relationships_target_entity_id_entity_objects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="fk_entity_relationships_created_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_entity_relationships"),
    )
    active_rows = sa.text("deleted_at IS NULL")
    op.create_index(
        "idx_relationships_workspace",
        "entity_relationships",
        ["workspace_id"],
        postgresql_where=active_rows,
    )
    op.create_index(
        "idx_relationships_source",
        "entity_relationships",
        ["source_entity_id"],
        postgresql_where=active_rows,
    )
    op.create_index(
        "idx_relationships_target",
        "entity_relationships",
        ["target_entity_id"],
        postgresql_where=active_rows,
    )
    op.create_index(
        "idx_relationships_type",
        "entity_relationships",
        ["relationship_type_id"],
        postgresql_where=active_rows,
    )


def downgrade() -> None:
    op.drop_index("idx_relationships_type", table_name="entity_relationships")
    op.drop_index("idx_relationships_target", table_name="entity_relationships")
    op.drop_index("idx_relationships_source", table_name="entity_relationships")
    op.drop_index("idx_relationships_workspace", table_name="entity_relationships")
    op.drop_table("entity_relationships")
    op.drop_index(
        "idx_relationship_types_workspace_active",
        table_name="relationship_types",
    )
    op.drop_table("relationship_types")
