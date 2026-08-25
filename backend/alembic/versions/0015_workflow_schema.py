"""Create versioned generic workflow persistence.

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def upgrade() -> None:
    created_at, updated_at = _timestamps()
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_by", sa.Uuid()),
        created_at,
        updated_at,
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "key", name="uq_workflow_definitions_workspace_key"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_workflow_definitions_id_workspace"),
    )
    op.create_index("idx_workflow_definitions_workspace", "workflow_definitions", ["workspace_id"])

    op.create_table(
        "workflow_definition_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("definition_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
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
        sa.Column("published_by", sa.Uuid()),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'RETIRED')", name="ck_workflow_versions_status"
        ),
        sa.ForeignKeyConstraint(
            ["definition_id", "workspace_id"],
            ["workflow_definitions.id", "workflow_definitions.workspace_id"],
            name="fk_workflow_versions_definition_workspace",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("definition_id", "version_number", name="uq_workflow_versions_number"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_workflow_versions_id_workspace"),
    )
    op.create_index(
        "idx_workflow_versions_workspace", "workflow_definition_versions", ["workspace_id"]
    )

    op.create_table(
        "workflow_state_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("definition_version_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("is_initial", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_terminal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["definition_version_id", "workspace_id"],
            ["workflow_definition_versions.id", "workflow_definition_versions.workspace_id"],
            name="fk_workflow_states_version_workspace",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("definition_version_id", "key", name="uq_workflow_states_version_key"),
        sa.UniqueConstraint(
            "id", "definition_version_id", "workspace_id", name="uq_workflow_states_scope"
        ),
    )

    op.create_table(
        "workflow_transition_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("definition_version_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("from_state_id", sa.Uuid(), nullable=False),
        sa.Column("to_state_id", sa.Uuid(), nullable=False),
        sa.Column("required_permission", sa.String(150), nullable=False),
        sa.Column("authority_kind", sa.String(80), nullable=False),
        sa.Column("assignment_kind", sa.String(80)),
        sa.Column("reason_required", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "policy", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["definition_version_id", "workspace_id"],
            ["workflow_definition_versions.id", "workflow_definition_versions.workspace_id"],
            name="fk_workflow_transitions_version_workspace",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["from_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_transitions_from_state_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_transitions_to_state_scope",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "definition_version_id", "key", name="uq_workflow_transitions_version_key"
        ),
        sa.UniqueConstraint(
            "id", "definition_version_id", "workspace_id", name="uq_workflow_transitions_scope"
        ),
    )

    op.create_table(
        "workflow_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("definition_version_id", sa.Uuid(), nullable=False),
        sa.Column("current_state_id", sa.Uuid(), nullable=False),
        sa.Column("target_kind", sa.String(80), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("target_version", sa.Integer()),
        sa.Column("started_by", sa.Uuid()),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(
            ["definition_version_id", "workspace_id"],
            ["workflow_definition_versions.id", "workflow_definition_versions.workspace_id"],
            name="fk_workflow_instances_version_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["current_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_instances_state_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["started_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "workspace_id", name="uq_workflow_instances_id_workspace"),
        sa.UniqueConstraint(
            "workspace_id", "target_kind", "target_id", name="uq_workflow_instances_target"
        ),
    )
    op.create_index(
        "idx_workflow_instances_workspace_state",
        "workflow_instances",
        ["workspace_id", "current_state_id"],
    )

    op.create_table(
        "workflow_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("instance_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_kind", sa.String(80), nullable=False),
        sa.Column("assigned_by", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["instance_id", "workspace_id"],
            ["workflow_instances.id", "workflow_instances.workspace_id"],
            name="fk_workflow_assignments_instance_workspace",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instance_id", "user_id", "assignment_kind", name="uq_workflow_assignments_actor_kind"
        ),
    )
    op.create_index(
        "idx_workflow_assignments_user", "workflow_assignments", ["workspace_id", "user_id"]
    )

    op.create_table(
        "workflow_transition_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("instance_id", sa.Uuid(), nullable=False),
        sa.Column("transition_id", sa.Uuid()),
        sa.Column("definition_version_id", sa.Uuid(), nullable=False),
        sa.Column("previous_state_id", sa.Uuid()),
        sa.Column("resulting_state_id", sa.Uuid(), nullable=False),
        sa.Column("action_key", sa.String(120), nullable=False),
        sa.Column("authority_kind", sa.String(80), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("target_version", sa.Integer()),
        sa.Column("resulting_instance_version", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column(
            "context", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["instance_id", "workspace_id"],
            ["workflow_instances.id", "workflow_instances.workspace_id"],
            name="fk_workflow_events_instance_workspace",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["transition_id", "definition_version_id", "workspace_id"],
            [
                "workflow_transition_definitions.id",
                "workflow_transition_definitions.definition_version_id",
                "workflow_transition_definitions.workspace_id",
            ],
            name="fk_workflow_events_transition_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["previous_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_events_previous_state_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["resulting_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_events_resulting_state_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "instance_id", "idempotency_key", name="uq_workflow_events_idempotency"
        ),
    )
    op.create_index(
        "idx_workflow_events_instance_time",
        "workflow_transition_events",
        ["instance_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_workflow_events_instance_time", table_name="workflow_transition_events")
    op.drop_table("workflow_transition_events")
    op.drop_index("idx_workflow_assignments_user", table_name="workflow_assignments")
    op.drop_table("workflow_assignments")
    op.drop_index("idx_workflow_instances_workspace_state", table_name="workflow_instances")
    op.drop_table("workflow_instances")
    op.drop_table("workflow_transition_definitions")
    op.drop_table("workflow_state_definitions")
    op.drop_index("idx_workflow_versions_workspace", table_name="workflow_definition_versions")
    op.drop_table("workflow_definition_versions")
    op.drop_index("idx_workflow_definitions_workspace", table_name="workflow_definitions")
    op.drop_table("workflow_definitions")
