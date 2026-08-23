"""Metadata-defined relationship persistence models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RelationshipType(Base):
    __tablename__ = "relationship_types"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_relationship_types_workspace_key"),
        CheckConstraint(
            "directionality IN ('DIRECTED', 'UNDIRECTED')",
            name="ck_relationship_types_directionality",
        ),
        Index("idx_relationship_types_workspace_active", "workspace_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)
    directionality: Mapped[str] = mapped_column(
        String(20), default="DIRECTED", server_default="DIRECTED"
    )
    source_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_types.id", ondelete="SET NULL")
    )
    target_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entity_types.id", ondelete="SET NULL")
    )
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"
    __table_args__ = (
        CheckConstraint(
            "source_entity_id <> target_entity_id",
            name="ck_entity_relationships_distinct_entities",
        ),
        Index(
            "idx_relationships_workspace",
            "workspace_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_relationships_source",
            "source_entity_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_relationships_target",
            "target_entity_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_relationships_type",
            "relationship_type_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    relationship_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("relationship_types.id", ondelete="RESTRICT")
    )
    source_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("entity_objects.id", ondelete="CASCADE")
    )
    target_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("entity_objects.id", ondelete="CASCADE")
    )
    attributes: Mapped[dict[str, object]] = mapped_column(
        JSONB(), default=dict, server_default=text("'{}'::jsonb")
    )
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
