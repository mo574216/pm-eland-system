"""Reusable import-profile and mapping API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

SystemImportField = Literal["name", "description", "parent_id"]


class ImportMappingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_sheet: str | None = Field(default=None, min_length=1, max_length=255)
    source_column: str = Field(min_length=1, max_length=255)
    target_attribute_definition_id: UUID | None = None
    target_system_field: SystemImportField | None = None
    transformation_config: dict[str, object] = Field(default_factory=dict)
    display_order: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def require_exactly_one_target(self) -> "ImportMappingInput":
        if (self.target_attribute_definition_id is None) == (self.target_system_field is None):
            raise ValueError("Exactly one mapping target is required.")
        return self


class ImportProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    entity_type_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    source_type: Literal["XLSX", "CSV"]
    configuration: dict[str, object] = Field(default_factory=dict)
    mappings: tuple[ImportMappingInput, ...] = Field(default=(), max_length=1_000)


class ImportProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    configuration: dict[str, object] | None = None
    mappings: tuple[ImportMappingInput, ...] | None = Field(default=None, max_length=1_000)

    @model_validator(mode="after")
    def require_mutation(self) -> "ImportProfileUpdate":
        if not {"name", "description", "configuration", "mappings"}.intersection(
            self.model_fields_set
        ):
            raise ValueError("At least one mutable profile field is required.")
        return self


class ImportMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_sheet: str | None
    source_column: str
    target_attribute_definition_id: UUID | None
    target_system_field: str | None
    transformation_config: dict[str, object]
    display_order: int


class ImportProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    entity_type_id: UUID
    name: str
    description: str | None
    source_type: str
    matching_strategy: dict[str, object]
    configuration: dict[str, object]
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    mappings: tuple[ImportMappingResponse, ...]


class ImportProfileListResponse(BaseModel):
    items: tuple[ImportProfileResponse, ...]
    page: int
    page_size: int
    total: int
