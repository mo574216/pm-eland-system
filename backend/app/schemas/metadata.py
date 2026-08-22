"""Metadata administration API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

STABLE_KEY_PATTERN = r"^[a-z][a-z0-9_]*$"


class EntityTypeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=180)
    plural_name: str | None = Field(default=None, max_length=180)
    description: str | None = None
    configuration: dict[str, object] = Field(default_factory=dict)


class EntityTypeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=180)
    plural_name: str | None = Field(default=None, max_length=180)
    description: str | None = None
    configuration: dict[str, object] | None = None
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_mutation(self) -> "EntityTypeUpdate":
        mutable = {"name", "plural_name", "description", "configuration"}
        if not mutable.intersection(self.model_fields_set):
            raise ValueError("At least one mutable entity-type field is required.")
        return self


class EntityTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    key: str
    name: str
    plural_name: str | None
    description: str | None
    icon_key: str | None
    is_active: bool
    configuration: dict[str, object]
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    version: int


class EntityTypeListResponse(BaseModel):
    items: tuple[EntityTypeResponse, ...]
    page: int
    page_size: int
    total: int
