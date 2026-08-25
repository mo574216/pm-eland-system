"""Generic versioned workflow definitions, instances, assignments, and events."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_workflow_definitions_workspace_key"),
        UniqueConstraint("id", "workspace_id", name="uq_workflow_definitions_id_workspace"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class WorkflowDefinitionVersion(Base):
    __tablename__ = "workflow_definition_versions"
    __table_args__ = (
        UniqueConstraint("definition_id", "version_number", name="uq_workflow_versions_number"),
        UniqueConstraint("id", "workspace_id", name="uq_workflow_versions_id_workspace"),
        CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'RETIRED')", name="ck_workflow_versions_status"
        ),
        ForeignKeyConstraint(
            ["definition_id", "workspace_id"],
            ["workflow_definitions.id", "workflow_definitions.workspace_id"],
            name="fk_workflow_versions_definition_workspace",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    definition_id: Mapped[UUID]
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", server_default="DRAFT")
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkflowStateDefinition(Base):
    __tablename__ = "workflow_state_definitions"
    __table_args__ = (
        UniqueConstraint("definition_version_id", "key", name="uq_workflow_states_version_key"),
        UniqueConstraint(
            "id", "definition_version_id", "workspace_id", name="uq_workflow_states_scope"
        ),
        ForeignKeyConstraint(
            ["definition_version_id", "workspace_id"],
            ["workflow_definition_versions.id", "workflow_definition_versions.workspace_id"],
            name="fk_workflow_states_version_workspace",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    definition_version_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(120))
    label: Mapped[str] = mapped_column(String(255))
    sequence_number: Mapped[int] = mapped_column(Integer)
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )


class WorkflowTransitionDefinition(Base):
    __tablename__ = "workflow_transition_definitions"
    __table_args__ = (
        UniqueConstraint(
            "definition_version_id", "key", name="uq_workflow_transitions_version_key"
        ),
        UniqueConstraint(
            "id", "definition_version_id", "workspace_id", name="uq_workflow_transitions_scope"
        ),
        ForeignKeyConstraint(
            ["definition_version_id", "workspace_id"],
            ["workflow_definition_versions.id", "workflow_definition_versions.workspace_id"],
            name="fk_workflow_transitions_version_workspace",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["from_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_transitions_from_state_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["to_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_transitions_to_state_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    definition_version_id: Mapped[UUID]
    key: Mapped[str] = mapped_column(String(120))
    label: Mapped[str] = mapped_column(String(255))
    from_state_id: Mapped[UUID]
    to_state_id: Mapped[UUID]
    required_permission: Mapped[str] = mapped_column(String(150))
    authority_kind: Mapped[str] = mapped_column(String(80))
    assignment_kind: Mapped[str | None] = mapped_column(String(80))
    reason_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    policy: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, server_default="{}")


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"
    __table_args__ = (
        UniqueConstraint("id", "workspace_id", name="uq_workflow_instances_id_workspace"),
        UniqueConstraint(
            "workspace_id", "target_kind", "target_id", name="uq_workflow_instances_target"
        ),
        ForeignKeyConstraint(
            ["definition_version_id", "workspace_id"],
            ["workflow_definition_versions.id", "workflow_definition_versions.workspace_id"],
            name="fk_workflow_instances_version_workspace",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["current_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_instances_state_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    definition_version_id: Mapped[UUID]
    current_state_id: Mapped[UUID]
    target_kind: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[UUID]
    target_version: Mapped[int | None] = mapped_column(Integer)
    started_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class WorkflowAssignment(Base):
    __tablename__ = "workflow_assignments"
    __table_args__ = (
        UniqueConstraint(
            "instance_id", "user_id", "assignment_kind", name="uq_workflow_assignments_actor_kind"
        ),
        ForeignKeyConstraint(
            ["instance_id", "workspace_id"],
            ["workflow_instances.id", "workflow_instances.workspace_id"],
            name="fk_workflow_assignments_instance_workspace",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    instance_id: Mapped[UUID]
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    assignment_kind: Mapped[str] = mapped_column(String(80))
    assigned_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkflowTransitionEvent(Base):
    __tablename__ = "workflow_transition_events"
    __table_args__ = (
        UniqueConstraint("instance_id", "idempotency_key", name="uq_workflow_events_idempotency"),
        ForeignKeyConstraint(
            ["instance_id", "workspace_id"],
            ["workflow_instances.id", "workflow_instances.workspace_id"],
            name="fk_workflow_events_instance_workspace",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["transition_id", "definition_version_id", "workspace_id"],
            [
                "workflow_transition_definitions.id",
                "workflow_transition_definitions.definition_version_id",
                "workflow_transition_definitions.workspace_id",
            ],
            name="fk_workflow_events_transition_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["previous_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_events_previous_state_scope",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["resulting_state_id", "definition_version_id", "workspace_id"],
            [
                "workflow_state_definitions.id",
                "workflow_state_definitions.definition_version_id",
                "workflow_state_definitions.workspace_id",
            ],
            name="fk_workflow_events_resulting_state_scope",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID]
    instance_id: Mapped[UUID]
    transition_id: Mapped[UUID | None]
    definition_version_id: Mapped[UUID]
    previous_state_id: Mapped[UUID | None]
    resulting_state_id: Mapped[UUID]
    action_key: Mapped[str] = mapped_column(String(120))
    authority_kind: Mapped[str] = mapped_column(String(80))
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    target_version: Mapped[int | None] = mapped_column(Integer)
    resulting_instance_version: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(Text)
    context: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict, server_default="{}")
    idempotency_key: Mapped[str] = mapped_column(String(255))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
