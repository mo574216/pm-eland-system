"""Generic relationship API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.metadata import STABLE_KEY_PATTERN


class RelationshipTypeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None
    directionality: Literal["DIRECTED", "UNDIRECTED"] = "DIRECTED"
    source_type_id: UUID | None = None
    target_type_id: UUID | None = None
    configuration: dict[str, object] = Field(default_factory=dict)


class RelationshipTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    key: str
    name: str
    description: str | None
    directionality: Literal["DIRECTED", "UNDIRECTED"]
    source_type_id: UUID | None
    target_type_id: UUID | None
    configuration: dict[str, object]
    is_active: bool
    created_at: datetime


class RelationshipTypeListResponse(BaseModel):
    items: tuple[RelationshipTypeResponse, ...]
    page: int
    page_size: int
    total: int


class RelationshipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_type_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    attributes: dict[str, object] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    relationship_type_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    attributes: dict[str, object]
    created_by: UUID | None
    created_at: datetime


class RelationshipListResponse(BaseModel):
    items: tuple[RelationshipResponse, ...]
    page: int
    page_size: int
    total: int
