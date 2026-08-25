"""Project phase API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.metadata import STABLE_KEY_PATTERN

PhaseStatus = Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "ARCHIVED"]


class PhaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str | None = Field(default=None, min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    sequence_number: int = Field(ge=1)


class PhaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    sequence_number: int | None = Field(default=None, ge=1)
    status: PhaseStatus | None = None
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_mutation(self) -> "PhaseUpdate":
        if not {"name", "description", "sequence_number", "status"}.intersection(
            self.model_fields_set
        ):
            raise ValueError("At least one mutable phase field is required.")
        return self


class PhaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    key: str
    name: str
    description: str | None
    sequence_number: int
    status: PhaseStatus
    is_locked: bool
    locked_by: UUID | None
    locked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int
