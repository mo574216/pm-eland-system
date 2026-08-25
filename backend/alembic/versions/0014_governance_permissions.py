"""Seed distinct governance permissions and baseline role profiles.

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-25
"""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, UUID, uuid5

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0014"
down_revision: str | Sequence[str] | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _seed_id(kind: str, code: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"pm-eland:{kind}:{code}")


PERMISSION_SEEDS = (
    (
        "DELIVERABLE_CONTRIBUTE",
        "deliverable",
        "contribute",
        "Prepare and revise assigned deliverable content.",
    ),
    (
        "DELIVERABLE_INTERNAL_REVIEW",
        "deliverable",
        "internal_review",
        "Perform contractor-side internal review and readiness decisions.",
    ),
    (
        "SUBMISSION_CREATE",
        "submission",
        "create",
        "Formally submit or resubmit an authorized immutable package.",
    ),
    (
        "PROJECT_MONITOR",
        "project",
        "monitor",
        "Monitor completeness, progress, and exceptions without decision authority.",
    ),
    ("PROJECT_REVIEW", "project_review", "review", "Perform project governance review."),
    (
        "PROJECT_RECOMMEND",
        "project_review",
        "recommend",
        "Record a project-manager recommendation.",
    ),
    (
        "TECHNICAL_REVIEW",
        "technical_review",
        "review",
        "Assess technical quality of an authorized immutable version.",
    ),
    (
        "TECHNICAL_SIGN_OFF",
        "technical_review",
        "sign_off",
        "Record an authorized technical sign-off without contractual acceptance.",
    ),
    (
        "ACCEPTANCE_DECIDE",
        "acceptance",
        "decide",
        "Record an employer phase or final acceptance decision.",
    ),
    (
        "CONDITION_VERIFY",
        "acceptance_condition",
        "verify",
        "Verify evidence for an assigned acceptance condition.",
    ),
    (
        "COMMUNICATION_MANAGE",
        "communication",
        "manage",
        "Create and manage authorized contextual project communications.",
    ),
    (
        "WORKFLOW_CONFIGURE",
        "workflow",
        "configure",
        "Configure and publish governed workflow definitions.",
    ),
)

ROLE_SEEDS = (
    (
        "PROJECT_OFFICER",
        "Project Officer",
        "Project monitoring, completeness follow-up, and reporting.",
    ),
    (
        "TECHNICAL_REVIEWER",
        "Technical Reviewer",
        "Independent technical assessment and configured sign-off.",
    ),
    (
        "CONTRACTOR_PROJECT_LEADER",
        "Contractor Project Leader",
        "Contractor-side execution, internal review, and formal submission.",
    ),
    (
        "CONTRACTOR_TEAM_MEMBER",
        "Contractor Team Member",
        "Preparation and revision of assigned contractor work.",
    ),
    (
        "EMPLOYER_REPRESENTATIVE",
        "Employer Representative",
        "Employer oversight and contractual acceptance authority.",
    ),
)

ROLE_GRANTS = {
    "SYSTEM_ADMIN": tuple(seed[0] for seed in PERMISSION_SEEDS),
    "PROJECT_MANAGER": (
        "PROJECT_MONITOR",
        "PROJECT_REVIEW",
        "PROJECT_RECOMMEND",
        "COMMUNICATION_MANAGE",
    ),
    "ANALYST": ("DELIVERABLE_CONTRIBUTE", "COMMUNICATION_MANAGE"),
    "PROJECT_OFFICER": (
        "WORKSPACE_READ",
        "ENTITY_READ",
        "DOCUMENT_READ",
        "DASHBOARD_READ",
        "AUDIT_READ",
        "PROJECT_MONITOR",
        "COMMUNICATION_MANAGE",
    ),
    "TECHNICAL_REVIEWER": (
        "WORKSPACE_READ",
        "ENTITY_READ",
        "DOCUMENT_READ",
        "DASHBOARD_READ",
        "TECHNICAL_REVIEW",
        "TECHNICAL_SIGN_OFF",
        "COMMUNICATION_MANAGE",
    ),
    "CONTRACTOR_PROJECT_LEADER": (
        "WORKSPACE_READ",
        "ENTITY_CREATE",
        "ENTITY_READ",
        "ENTITY_UPDATE",
        "FORM_SUBMIT",
        "DOCUMENT_UPLOAD",
        "DOCUMENT_READ",
        "DASHBOARD_READ",
        "DELIVERABLE_CONTRIBUTE",
        "DELIVERABLE_INTERNAL_REVIEW",
        "SUBMISSION_CREATE",
        "PROJECT_MONITOR",
        "COMMUNICATION_MANAGE",
    ),
    "CONTRACTOR_TEAM_MEMBER": (
        "WORKSPACE_READ",
        "ENTITY_READ",
        "ENTITY_UPDATE",
        "FORM_SUBMIT",
        "DOCUMENT_UPLOAD",
        "DOCUMENT_READ",
        "DASHBOARD_READ",
        "DELIVERABLE_CONTRIBUTE",
        "COMMUNICATION_MANAGE",
    ),
    "EMPLOYER_REPRESENTATIVE": (
        "WORKSPACE_READ",
        "ENTITY_READ",
        "DOCUMENT_READ",
        "DASHBOARD_READ",
        "AUDIT_READ",
        "PROJECT_MONITOR",
        "ACCEPTANCE_DECIDE",
        "CONDITION_VERIFY",
        "COMMUNICATION_MANAGE",
    ),
}


def upgrade() -> None:
    connection = op.get_bind()
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

    role_values = [
        {
            "id": _seed_id("role", code),
            "code": code,
            "name": name,
            "description": description,
            "is_system": True,
        }
        for code, name, description in ROLE_SEEDS
    ]
    role_insert = postgresql.insert(roles).values(role_values)
    connection.execute(
        role_insert.on_conflict_do_update(
            index_elements=[roles.c.code],
            set_={
                "name": role_insert.excluded.name,
                "description": role_insert.excluded.description,
            },
        )
    )
    permission_values = [
        {
            "id": _seed_id("permission", code),
            "code": code,
            "resource": resource,
            "action": action,
            "description": description,
        }
        for code, resource, action, description in PERMISSION_SEEDS
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

    role_ids = dict(connection.execute(sa.select(roles.c.code, roles.c.id)).all())
    permission_ids = dict(connection.execute(sa.select(permissions.c.code, permissions.c.id)).all())
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


def downgrade() -> None:
    connection = op.get_bind()
    new_role_codes = tuple(seed[0] for seed in ROLE_SEEDS)
    new_permission_codes = tuple(seed[0] for seed in PERMISSION_SEEDS)
    connection.execute(
        sa.text("DELETE FROM roles WHERE code = ANY(:codes)").bindparams(codes=list(new_role_codes))
    )
    connection.execute(
        sa.text("DELETE FROM permissions WHERE code = ANY(:codes)").bindparams(
            codes=list(new_permission_codes)
        )
    )
