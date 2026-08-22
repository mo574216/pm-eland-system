"""Metadata definitions for configurable entity types and attributes."""

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


class EntityType(Base):
    __tablename__ = "entity_types"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_entity_types_workspace_key"),
        Index("idx_entity_types_workspace", "workspace_id"),
        Index("idx_entity_types_active", "workspace_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(180))
    plural_name: Mapped[str | None] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    icon_key: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")


class AttributeDefinition(Base):
    __tablename__ = "attribute_definitions"
    __table_args__ = (
        UniqueConstraint("entity_type_id", "key", name="uq_attribute_definitions_type_key"),
        CheckConstraint(
            "data_type IN (" + ", ".join(f"'{value}'" for value in SUPPORTED_ATTRIBUTE_TYPES) + ")",
            name="ck_attribute_definitions_data_type",
        ),
        Index("idx_attribute_definitions_type", "entity_type_id"),
        Index("idx_attribute_definitions_active", "entity_type_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    entity_type_id: Mapped[UUID] = mapped_column(ForeignKey("entity_types.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(120))
    label: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    data_type: Mapped[str] = mapped_column(String(40))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_read_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    default_value: Mapped[object | None] = mapped_column(JSONB())
    validation_config: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    display_config: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    inheritance_config: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
