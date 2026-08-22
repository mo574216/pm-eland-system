"""Metadata administration API schemas."""

from datetime import datetime
from typing import Literal
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


AttributeDataType = Literal[
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
]


class AttributeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    label: str = Field(min_length=1, max_length=180)
    description: str | None = None
    data_type: AttributeDataType
    is_required: bool = False
    is_read_only: bool = False
    default_value: object | None = None
    validation_config: dict[str, object] = Field(default_factory=dict)
    display_config: dict[str, object] = Field(default_factory=dict)
    inheritance_config: dict[str, object] = Field(default_factory=dict)
    display_order: int = Field(default=0, ge=0)


class AttributeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    label: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = None
    is_required: bool | None = None
    is_read_only: bool | None = None
    default_value: object | None = None
    validation_config: dict[str, object] | None = None
    display_config: dict[str, object] | None = None
    inheritance_config: dict[str, object] | None = None
    display_order: int | None = Field(default=None, ge=0)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_mutation(self) -> "AttributeUpdate":
        mutable = {
            "label",
            "description",
            "is_required",
            "is_read_only",
            "default_value",
            "validation_config",
            "display_config",
            "inheritance_config",
            "display_order",
        }
        if not mutable.intersection(self.model_fields_set):
            raise ValueError("At least one mutable attribute field is required.")
        return self


class AttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    entity_type_id: UUID
    key: str
    label: str
    description: str | None
    data_type: AttributeDataType
    is_required: bool
    is_read_only: bool
    default_value: object | None
    validation_config: dict[str, object]
    display_config: dict[str, object]
    inheritance_config: dict[str, object]
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    version: int
