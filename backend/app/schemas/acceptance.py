"""Contracts for phase acceptance packages, decisions, and conditions."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AcceptancePackageCreate(BaseModel):
    employer_recipient_id: UUID
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class AcceptanceConditionCreate(BaseModel):
    description: Annotated[str, Field(min_length=1, max_length=5000)]
    responsible_id: UUID
    verifier_id: UUID
    due_at: datetime
    evidence_requirement: Annotated[str, Field(min_length=1, max_length=5000)]
    mandatory: bool = True


class AcceptanceDecisionCreate(BaseModel):
    decision_kind: Literal["ACCEPT", "CONDITIONAL_ACCEPT", "REJECT"]
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    conditions: Annotated[list[AcceptanceConditionCreate], Field(max_length=100)] = []
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]

    @model_validator(mode="after")
    def validate_conditions(self) -> "AcceptanceDecisionCreate":
        if self.decision_kind == "CONDITIONAL_ACCEPT" and not self.conditions:
            raise ValueError("conditional acceptance requires at least one condition")
        if self.decision_kind != "CONDITIONAL_ACCEPT" and self.conditions:
            raise ValueError("conditions are only valid for conditional acceptance")
        return self


class AcceptanceEvidenceItem(BaseModel):
    resource_kind: Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"]
    resource_id: UUID


class AcceptanceConditionEvidenceCreate(BaseModel):
    expected_version: int = Field(ge=1)
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    evidence: Annotated[list[AcceptanceEvidenceItem], Field(min_length=1, max_length=100)]
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class AcceptanceConditionVerificationCreate(BaseModel):
    expected_version: int = Field(ge=1)
    decision: Literal["VERIFY", "REJECT_EVIDENCE"]
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class AcceptanceClosureCreate(BaseModel):
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class AcceptancePackageItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    deliverable_version_id: UUID
    review_outcome_ids: list[UUID]
    label_snapshot: str


class AcceptanceConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    responsible_id: UUID | None
    verifier_id: UUID | None
    due_at: datetime
    evidence_requirement: str
    mandatory: bool
    status: str
    version: int
    available_actions: list[str] = []


class AcceptanceDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision_kind: str
    actor_id: UUID | None
    authority_kind: str
    statement: str
    decided_at: datetime
    conditions: list[AcceptanceConditionResponse] = []
    closed_at: datetime | None = None
    closure_statement: str | None = None
    can_close: bool = False


class AcceptancePackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    phase_id: UUID
    sequence_number: int
    statement: str
    employer_recipient_id: UUID | None
    requested_by: UUID | None
    created_at: datetime
    items: list[AcceptancePackageItemResponse] = []
    decision: AcceptanceDecisionResponse | None = None
    available_decisions: list[str] = []


class AcceptanceWorkspaceResponse(BaseModel):
    can_prepare: bool
    packages: list[AcceptancePackageResponse]
