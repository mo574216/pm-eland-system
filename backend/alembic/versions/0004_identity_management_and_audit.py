"""Add identity management permission and append-only audit storage.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-22
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

IDENTITY_MANAGE_ID = UUID("69521d82-ad35-5bb5-8690-fd479a18d6a4")
SYSTEM_ADMIN_ID = UUID("7fd2f310-4dcf-5f27-b917-22e6f4a29bc7")


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid()),
        sa.Column("workspace_id", sa.Uuid()),
        sa.Column("user_id", sa.Uuid()),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.Uuid()),
        sa.Column("source", sa.String(length=40), server_default="API", nullable=False),
        sa.Column("before_state", postgresql.JSONB()),
        sa.Column("after_state", postgresql.JSONB()),
        sa.Column("client_ip", postgresql.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index(
        "idx_audit_workspace_time", "audit_logs", ["workspace_id", sa.text("created_at DESC")]
    )
    op.create_index(
        "idx_audit_resource",
        "audit_logs",
        ["resource_type", "resource_id", sa.text("created_at DESC")],
    )
    op.create_index("idx_audit_user", "audit_logs", ["user_id", sa.text("created_at DESC")])

    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("description", sa.Text()),
    )
    permission_insert = postgresql.insert(permissions).values(
        id=IDENTITY_MANAGE_ID,
        code="IDENTITY_MANAGE",
        resource="identity",
        action="manage",
        description="Assign and remove global user roles.",
    )
    op.get_bind().execute(
        permission_insert.on_conflict_do_update(
            index_elements=[permissions.c.code],
            set_={
                "resource": permission_insert.excluded.resource,
                "action": permission_insert.excluded.action,
                "description": permission_insert.excluded.description,
            },
        )
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )
    op.get_bind().execute(
        postgresql.insert(role_permissions)
        .values(role_id=SYSTEM_ADMIN_ID, permission_id=IDENTITY_MANAGE_ID)
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM permissions WHERE code = :code").bindparams(code="IDENTITY_MANAGE")
    )
    op.drop_index("idx_audit_user", table_name="audit_logs")
    op.drop_index("idx_audit_resource", table_name="audit_logs")
    op.drop_index("idx_audit_workspace_time", table_name="audit_logs")
    op.drop_table("audit_logs")
