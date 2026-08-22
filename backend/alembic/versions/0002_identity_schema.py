"""Create the identity and global RBAC schema.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-22
"""

from collections.abc import Sequence
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROLE_SEEDS = (
    {
        "id": UUID("7fd2f310-4dcf-5f27-b917-22e6f4a29bc7"),
        "code": "SYSTEM_ADMIN",
        "name": "System Administrator",
        "description": "Full platform administration.",
        "is_system": True,
    },
    {
        "id": UUID("20118650-ea67-51b8-b282-a3e92631d466"),
        "code": "PROJECT_MANAGER",
        "name": "Project Manager",
        "description": "Workspace/project management and review.",
        "is_system": True,
    },
    {
        "id": UUID("f7443d96-7d9a-5a25-89bb-38c05971e2e5"),
        "code": "ANALYST",
        "name": "Analyst",
        "description": "Structured data and document contribution.",
        "is_system": True,
    },
    {
        "id": UUID("ba9956f7-d7d1-581d-bb3b-d8af14c36e48"),
        "code": "VIEWER",
        "name": "Viewer",
        "description": "Read-only access.",
        "is_system": True,
    },
)

PERMISSION_SEEDS = (
    (
        "d5670ed6-78c1-510d-94b5-32bc5dc3fec0",
        "WORKSPACE_CREATE",
        "workspace",
        "create",
        "Create a workspace.",
    ),
    (
        "356c9ecb-b9ff-5cbe-81bb-4b714d9e489b",
        "WORKSPACE_READ",
        "workspace",
        "read",
        "Read accessible workspace information.",
    ),
    (
        "e9126be6-27d3-5b95-ac7e-13d0d040d2ec",
        "WORKSPACE_MANAGE",
        "workspace",
        "manage",
        "Modify workspace configuration and membership.",
    ),
    (
        "38c64dc3-888e-5fc6-ab63-231ca56f5778",
        "ENTITY_CREATE",
        "entity",
        "create",
        "Create generic entities.",
    ),
    (
        "bdb0881e-7fa5-5e8b-ad95-a5e361579f87",
        "ENTITY_READ",
        "entity",
        "read",
        "Read accessible entities.",
    ),
    (
        "c733228f-240c-509b-8d32-157f8de9d72f",
        "ENTITY_UPDATE",
        "entity",
        "update",
        "Update mutable generic entities.",
    ),
    (
        "fd04a94e-12d5-5ac3-916b-e93b09c403e6",
        "ENTITY_ARCHIVE",
        "entity",
        "archive",
        "Archive or soft-delete entities.",
    ),
    (
        "cc2b7cd1-62ee-57df-8877-f91e06753dd0",
        "RELATIONSHIP_MANAGE",
        "relationship",
        "manage",
        "Create and remove entity relationships.",
    ),
    (
        "be11a775-b0b6-5a7c-8895-e2774c3997f9",
        "METADATA_MANAGE",
        "metadata",
        "manage",
        "Manage entity types, attributes, and related metadata.",
    ),
    (
        "e342df59-debf-5b9c-b0c1-b9e398eea29d",
        "FORM_DESIGN",
        "form",
        "design",
        "Create, configure, version, and publish forms.",
    ),
    (
        "5301b56b-4ce1-56d0-9234-abd668772f72",
        "FORM_SUBMIT",
        "form_instance",
        "submit",
        "Create/update/submit form instances.",
    ),
    (
        "7a99a452-8fb4-5d08-a5f8-94f0839f4f03",
        "DOCUMENT_UPLOAD",
        "document",
        "upload",
        "Upload logical documents and new versions.",
    ),
    (
        "dd8dc3b3-2e2c-5a8b-b722-80fd863cbe59",
        "DOCUMENT_READ",
        "document",
        "read",
        "Read/download/preview authorized documents.",
    ),
    (
        "f51f5d80-8caf-57c9-bf29-9666348c6c21",
        "DOCUMENT_ARCHIVE",
        "document",
        "archive",
        "Archive logical documents.",
    ),
    (
        "9957b1ed-2c91-51f2-b1ee-f54e9d52e249",
        "IMPORT_EXECUTE",
        "import",
        "execute",
        "Upload, dry-run, resolve, and commit imports.",
    ),
    (
        "e38ebfab-21b5-5b9b-8749-1f03ad52ecfa",
        "PHASE_MANAGE",
        "phase",
        "manage",
        "Create/update phases and deliverables.",
    ),
    ("7682b350-ea7e-5e4d-a002-a2be969bfe6f", "PHASE_LOCK", "phase", "lock", "Lock a phase."),
    ("57057938-1a6b-5c9b-b092-104c8f0c68cd", "PHASE_UNLOCK", "phase", "unlock", "Unlock a phase."),
    (
        "cb3c351a-af26-58cc-b7c3-f89c4914c46f",
        "REVIEW_MANAGE",
        "review",
        "manage",
        "Add review comments, resolve comments, and request revisions.",
    ),
    (
        "d42f1de3-8838-5b68-9245-184bfc0e5ff0",
        "DASHBOARD_READ",
        "dashboard",
        "read",
        "View dashboards.",
    ),
    (
        "a0ebac85-e21b-5359-80f3-7769078f93de",
        "DASHBOARD_MANAGE",
        "dashboard",
        "manage",
        "Create and configure dashboards.",
    ),
    (
        "d3cf2595-03f7-5489-aadb-d314e1627c7c",
        "AUDIT_READ",
        "audit",
        "read",
        "View authorized audit history.",
    ),
)

ROLE_GRANTS = {
    "SYSTEM_ADMIN": tuple(permission[1] for permission in PERMISSION_SEEDS),
    "PROJECT_MANAGER": (
        "WORKSPACE_READ",
        "ENTITY_CREATE",
        "ENTITY_READ",
        "ENTITY_UPDATE",
        "RELATIONSHIP_MANAGE",
        "FORM_SUBMIT",
        "DOCUMENT_UPLOAD",
        "DOCUMENT_READ",
        "IMPORT_EXECUTE",
        "PHASE_MANAGE",
        "PHASE_LOCK",
        "PHASE_UNLOCK",
        "REVIEW_MANAGE",
        "DASHBOARD_READ",
        "DASHBOARD_MANAGE",
        "AUDIT_READ",
    ),
    "ANALYST": (
        "WORKSPACE_READ",
        "ENTITY_CREATE",
        "ENTITY_READ",
        "ENTITY_UPDATE",
        "RELATIONSHIP_MANAGE",
        "FORM_SUBMIT",
        "DOCUMENT_UPLOAD",
        "DOCUMENT_READ",
        "IMPORT_EXECUTE",
        "DASHBOARD_READ",
    ),
    "VIEWER": ("WORKSPACE_READ", "ENTITY_READ", "DOCUMENT_READ", "DASHBOARD_READ"),
}


def seed_identity_data(connection: Connection) -> None:
    """Synchronize immutable system roles, permissions, and grants idempotently."""
    roles = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_system", sa.Boolean()),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String()),
        sa.column("resource", sa.String()),
        sa.column("action", sa.String()),
        sa.column("description", sa.Text()),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Uuid()),
        sa.column("permission_id", sa.Uuid()),
    )

    role_insert = postgresql.insert(roles).values(ROLE_SEEDS)
    connection.execute(
        role_insert.on_conflict_do_update(
            index_elements=[roles.c.code],
            set_={
                "name": role_insert.excluded.name,
                "description": role_insert.excluded.description,
                "is_system": role_insert.excluded.is_system,
            },
        )
    )

    permission_values = [
        {
            "id": UUID(identifier),
            "code": code,
            "resource": resource,
            "action": action,
            "description": description,
        }
        for identifier, code, resource, action, description in PERMISSION_SEEDS
    ]
    permission_insert = postgresql.insert(permissions).values(permission_values)
    connection.execute(
        permission_insert.on_conflict_do_update(
            index_elements=[permissions.c.code],
            set_={
                "resource": permission_insert.excluded.resource,
                "action": permission_insert.excluded.action,
                "description": permission_insert.excluded.description,
            },
        )
    )

    role_ids = {role["code"]: role["id"] for role in ROLE_SEEDS}
    permission_ids = {permission[1]: UUID(permission[0]) for permission in PERMISSION_SEEDS}
    grant_values = [
        {"role_id": role_ids[role_code], "permission_id": permission_ids[permission_code]}
        for role_code, grants in ROLE_GRANTS.items()
        for permission_code in grants
    ]
    connection.execute(
        postgresql.insert(role_permissions)
        .values(grant_values)
        .on_conflict_do_nothing(
            index_elements=[role_permissions.c.role_id, role_permissions.c.permission_id]
        )
    )


def upgrade() -> None:
    """Create identity tables and install the canonical RBAC registry."""
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", postgresql.CITEXT(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("first_name", sa.String(length=120)),
        sa.Column("last_name", sa.String(length=120)),
        sa.Column("display_name", sa.String(length=255)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_active", "users", ["is_active"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_system", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=150), nullable=False),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_permissions"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
        sa.UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_user_roles_role_id_roles", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_role_permissions_role_id_roles", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_role_permissions_permission_id_permissions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
    )
    seed_identity_data(op.get_bind())


def downgrade() -> None:
    """Remove identity tables in reverse dependency order."""
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index("idx_users_active", table_name="users")
    op.drop_table("users")
