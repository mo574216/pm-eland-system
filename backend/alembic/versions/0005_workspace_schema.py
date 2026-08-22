"""Create workspace isolation and membership schema.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("owner_id", sa.Uuid()),
        sa.Column("status", sa.String(length=30), server_default="DRAFT", nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')",
            name="ck_workspaces_status",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name="fk_workspaces_owner_id_users", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workspaces"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_index("idx_workspaces_status", "workspaces", ["status"])
    op.create_index("idx_workspaces_owner", "workspaces", ["owner_id"])

    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid()),
        sa.Column("status", sa.String(length=30), server_default="ACTIVE", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED')",
            name="ck_workspace_memberships_status",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_workspace_memberships_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_workspace_memberships_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_workspace_memberships_role_id_roles",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workspace_memberships"),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_memberships_workspace_user",
        ),
    )
    op.create_index("idx_workspace_memberships_user", "workspace_memberships", ["user_id"])
    op.create_index(
        "idx_workspace_memberships_workspace", "workspace_memberships", ["workspace_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_workspace_memberships_workspace", table_name="workspace_memberships")
    op.drop_index("idx_workspace_memberships_user", table_name="workspace_memberships")
    op.drop_table("workspace_memberships")
    op.drop_index("idx_workspaces_owner", table_name="workspaces")
    op.drop_index("idx_workspaces_status", table_name="workspaces")
    op.drop_table("workspaces")
