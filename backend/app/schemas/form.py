"""Draft form definition and field API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.metadata import STABLE_KEY_PATTERN

FormLifecycleStatus = Literal["DRAFT", "PUBLISHED", "RETIRED"]
FormFieldType = Literal[
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
    "TABLE",
]


class FormSectionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    label: str = Field(min_length=1, max_length=180)
    display_order: int = Field(default=0, ge=0)
    configuration: dict[str, object] = Field(default_factory=dict)


class FormSchemaDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: tuple[FormSectionDefinition, ...] = ()

    @model_validator(mode="after")
    def unique_section_keys(self) -> "FormSchemaDefinition":
        keys = [section.key for section in self.sections]
        if len(keys) != len(set(keys)):
            raise ValueError("Section keys must be unique.")
        return self


class FormCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=255)
    entity_type_id: UUID | None = None
    description: str | None = None


class FormUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    entity_type_id: UUID | None = None
    description: str | None = None
    schema_definition: FormSchemaDefinition | None = Field(default=None, alias="schema_json")

    @model_validator(mode="after")
    def require_mutation(self) -> "FormUpdate":
        if not {"name", "entity_type_id", "description", "schema_definition"}.intersection(
            self.model_fields_set
        ):
            raise ValueError("At least one mutable form field is required.")
        return self


class FormFieldCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    label: str = Field(min_length=1, max_length=180)
    field_type: FormFieldType
    attribute_definition_id: UUID | None = None
    section_key: str | None = Field(default=None, max_length=120, pattern=STABLE_KEY_PATTERN)
    display_order: int = Field(default=0, ge=0)
    is_required: bool = False
    is_read_only: bool = False
    configuration: dict[str, object] = Field(default_factory=dict)
    visibility_rule: dict[str, object] = Field(default_factory=dict)
    validation_rule: dict[str, object] = Field(default_factory=dict)
    inheritance_rule: dict[str, object] = Field(default_factory=dict)


class FormFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    form_definition_id: UUID
    attribute_definition_id: UUID | None
    key: str
    label: str
    field_type: FormFieldType
    section_key: str | None
    display_order: int
    is_required: bool
    is_read_only: bool
    configuration: dict[str, object]
    visibility_rule: dict[str, object]
    validation_rule: dict[str, object]
    inheritance_rule: dict[str, object]


class FormSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    entity_type_id: UUID | None
    key: str
    name: str
    description: str | None
    version_number: int
    lifecycle_status: FormLifecycleStatus
    created_by: UUID | None
    created_at: datetime
    published_at: datetime | None
    retired_at: datetime | None


class FormDefinitionResponse(FormSummaryResponse):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    schema_definition: FormSchemaDefinition = Field(alias="schema_json")
    fields: tuple[FormFieldResponse, ...]


class FormListResponse(BaseModel):
    items: tuple[FormSummaryResponse, ...]
    page: int
    page_size: int
    total: int
