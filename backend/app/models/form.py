"""Metadata-driven form definition, field, and instance models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FormDefinition(Base):
    __tablename__ = "form_definitions"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "key",
            "version_number",
            name="uq_form_definitions_workspace_key_version",
        ),
        CheckConstraint("version_number > 0", name="ck_form_definitions_version_positive"),
        CheckConstraint(
            "lifecycle_status IN ('DRAFT', 'PUBLISHED', 'RETIRED')",
            name="ck_form_definitions_lifecycle_status",
        ),
        Index(
            "idx_form_definitions_workspace_status",
            "workspace_id",
            "lifecycle_status",
        ),
        Index("idx_form_definitions_entity_type", "entity_type_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    entity_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_types.id", ondelete="RESTRICT")
    )
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    version_number: Mapped[int] = mapped_column(Integer)
    lifecycle_status: Mapped[str] = mapped_column(
        String(30), default="DRAFT", server_default="DRAFT"
    )
    schema_json: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FormField(Base):
    __tablename__ = "form_fields"
    __table_args__ = (
        UniqueConstraint("form_definition_id", "key", name="uq_form_fields_definition_key"),
        Index(
            "idx_form_fields_definition_order",
            "form_definition_id",
            "display_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    form_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("form_definitions.id", ondelete="CASCADE")
    )
    attribute_definition_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attribute_definitions.id", ondelete="SET NULL")
    )
    key: Mapped[str] = mapped_column(String(120))
    label: Mapped[str] = mapped_column(String(180))
    field_type: Mapped[str] = mapped_column(String(40))
    section_key: Mapped[str | None] = mapped_column(String(120))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_read_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    visibility_rule: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    validation_rule: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    inheritance_rule: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )


class FormInstance(Base):
    __tablename__ = "form_instances"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REVISION_REQUESTED')",
            name="ck_form_instances_status",
        ),
        CheckConstraint("version > 0", name="ck_form_instances_version_positive"),
        Index("idx_form_instances_workspace", "workspace_id"),
        Index("idx_form_instances_entity", "entity_id"),
        Index("idx_form_instances_form", "form_definition_id"),
        Index("idx_form_instances_values_gin", "values_json", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    form_definition_id: Mapped[UUID] = mapped_column(
        ForeignKey("form_definitions.id", ondelete="RESTRICT")
    )
    entity_id: Mapped[UUID] = mapped_column(ForeignKey("entity_objects.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", server_default="DRAFT")
    values_json: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    submitted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
