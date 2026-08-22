"""Generic metadata-defined entity object model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EntityObject(Base):
    __tablename__ = "entity_objects"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'ARCHIVED', 'DELETED')",
            name="ck_entity_objects_status",
        ),
        Index(
            "idx_entity_objects_workspace",
            "workspace_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_entity_objects_type",
            "workspace_id",
            "entity_type_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_entity_objects_parent",
            "parent_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("idx_entity_objects_name", "workspace_id", "name"),
        Index("idx_entity_objects_attributes_gin", "attributes", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    entity_type_id: Mapped[UUID] = mapped_column(ForeignKey("entity_types.id", ondelete="RESTRICT"))
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_objects.id", ondelete="RESTRICT")
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE", server_default="ACTIVE")
    attributes: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
