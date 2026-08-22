"""Workspace API request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WorkspaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=160)
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_mutation(self) -> "WorkspaceUpdate":
        if "name" not in self.model_fields_set and "description" not in self.model_fields_set:
            raise ValueError("At least one mutable workspace field is required.")
        return self


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    owner_id: UUID | None
    status: str
    configuration: dict[str, object]
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    version: int


class WorkspaceListResponse(BaseModel):
    items: tuple[WorkspaceResponse, ...]
    page: int
    page_size: int
    total: int


class WorkspaceMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    role_id: UUID


class WorkspaceMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    display_name: str | None
    role_id: UUID | None
    role_code: str | None
    status: str
    created_at: datetime
