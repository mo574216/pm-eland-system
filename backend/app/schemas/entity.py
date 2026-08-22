"""Generic entity-object API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EntityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    entity_type_id: UUID
    parent_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    attributes: dict[str, object] = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    attributes: dict[str, object] | None = None
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_mutation(self) -> "EntityUpdate":
        if not {"name", "description", "attributes"}.intersection(self.model_fields_set):
            raise ValueError("At least one mutable entity field is required.")
        return self


class EntityTypeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    name: str


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    entity_type_id: UUID
    entity_type: EntityTypeSummary
    parent_id: UUID | None
    name: str
    description: str | None
    status: str
    attributes: dict[str, object]
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version: int


class EntityListResponse(BaseModel):
    items: tuple[EntityResponse, ...]
    page: int
    page_size: int
    total: int


class EntityTreeTypeSummary(BaseModel):
    id: UUID
    key: str
    name: str
    icon_key: str | None = None


class EntityTreeNode(BaseModel):
    id: UUID
    workspace_id: UUID
    entity_type_id: UUID
    entity_type: EntityTreeTypeSummary | None
    parent_id: UUID | None
    name: str
    status: str
    depth: int = Field(ge=0)
    path: tuple[UUID, ...]
    has_children: bool


class EntityTreeResponse(BaseModel):
    items: tuple[EntityTreeNode, ...]
    root_id: UUID | None
    depth: int | None
