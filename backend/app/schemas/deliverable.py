"""Contracts for generic deliverables and immutable formal submissions."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.workflow import WorkflowInstanceResponse


class DeliverableRequirement(BaseModel):
    key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,119}$")]
    label: Annotated[str, Field(min_length=1, max_length=255)]
    resource_kind: Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"]
    required: bool = True


class DeliverableCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255)]
    description: Annotated[str | None, Field(max_length=5000)] = None
    owner_id: UUID
    contributor_ids: Annotated[list[UUID], Field(max_length=100)] = []
    internal_reviewer_id: UUID
    internal_due_at: datetime | None = None
    official_due_at: datetime | None = None
    requirements: Annotated[list[DeliverableRequirement], Field(max_length=100)] = []

    @model_validator(mode="after")
    def validate_dates_and_requirements(self) -> "DeliverableCreate":
        if (
            self.internal_due_at is not None
            and self.official_due_at is not None
            and self.internal_due_at > self.official_due_at
        ):
            raise ValueError("internal_due_at must not be after official_due_at")
        keys = [item.key for item in self.requirements]
        if len(keys) != len(set(keys)):
            raise ValueError("requirement keys must be unique")
        return self


class DeliverablePackageItemCreate(BaseModel):
    resource_kind: Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"]
    resource_id: UUID
    requirement_key: Annotated[str | None, Field(max_length=120)] = None


class PackageResourceOption(BaseModel):
    id: UUID
    resource_kind: Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"]
    label: str
    resource_version: int | None


class DeliverableAssigneeOption(BaseModel):
    user_id: UUID
    username: str
    display_name: str | None
    role_code: str | None


class DeliverableVersionCreate(BaseModel):
    summary: Annotated[str | None, Field(max_length=5000)] = None
    items: Annotated[list[DeliverablePackageItemCreate], Field(min_length=1, max_length=200)]


class SubmissionCreate(BaseModel):
    deliverable_version_id: UUID
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    recipient_ids: Annotated[list[UUID], Field(min_length=1, max_length=100)]
    related_comment_ids: Annotated[list[UUID], Field(max_length=100)] = []
    prior_submission_id: UUID | None = None
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class SubmissionWithdrawalCreate(BaseModel):
    reason: Annotated[str, Field(min_length=1, max_length=5000)]
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class ReviewCommentCreate(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=10000)]
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]


class ReviewOutcomeCreate(BaseModel):
    outcome_kind: Literal[
        "CLARIFICATION",
        "REVISION_REQUEST",
        "RECOMMENDATION",
        "CONDITIONAL_RECOMMENDATION",
        "REJECTION_MAJOR_REVISION",
        "TECHNICAL_SIGN_OFF",
    ]
    authority_kind: Literal["PROJECT_REVIEW", "TECHNICAL_REVIEW"]
    statement: Annotated[str, Field(min_length=1, max_length=10000)]
    conditions: Annotated[list[str], Field(max_length=100)] = []
    related_comment_ids: Annotated[list[UUID], Field(max_length=100)] = []
    expected_workflow_version: int | None = Field(default=None, ge=1)
    idempotency_key: Annotated[str, Field(min_length=1, max_length=255)]

    @model_validator(mode="after")
    def validate_outcome(self) -> "ReviewOutcomeCreate":
        if self.outcome_kind == "CONDITIONAL_RECOMMENDATION" and not self.conditions:
            raise ValueError("conditions are required for a conditional recommendation")
        if self.outcome_kind == "TECHNICAL_SIGN_OFF" and self.authority_kind != "TECHNICAL_REVIEW":
            raise ValueError("technical sign-off requires technical review authority")
        if self.outcome_kind == "REVISION_REQUEST" and self.expected_workflow_version is None:
            raise ValueError("expected_workflow_version is required for a revision request")
        return self


class PackageItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource_kind: str
    resource_id: UUID
    resource_version: int | None
    label_snapshot: str
    is_required: bool
    metadata_snapshot: dict[str, object]


class DeliverableVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    summary: str | None
    created_by: UUID | None
    created_at: datetime
    items: list[PackageItemResponse] = []


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deliverable_version_id: UUID
    sequence_number: int
    submission_kind: str
    prior_submission_id: UUID | None
    submitter_id: UUID | None
    statement: str
    recipient_ids: list[UUID] = []
    submitted_at: datetime
    withdrawn_at: datetime | None = None
    withdrawal_reason: str | None = None
    review_comments: list["ReviewCommentResponse"] = []
    review_outcomes: list["ReviewOutcomeResponse"] = []
    available_review_actions: list["ReviewActionResponse"] = []


class ReviewCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    deliverable_version_id: UUID
    author_id: UUID | None
    text: str
    status: str
    created_at: datetime


class ReviewOutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    deliverable_version_id: UUID
    outcome_kind: str
    authority_kind: str
    actor_id: UUID | None
    statement: str
    conditions: list[str]
    related_comment_ids: list[UUID]
    created_at: datetime


class ReviewActionResponse(BaseModel):
    outcome_kind: str
    authority_kind: str
    label: str
    changes_workflow: bool = False


class DeliverableReadiness(BaseModel):
    ready: bool
    total_required: int
    completed_required: int
    missing: list[str]


class DeliverableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    phase_id: UUID
    key: str
    name: str
    description: str | None
    owner_id: UUID | None
    internal_reviewer_id: UUID | None
    contributor_ids: list[UUID] = []
    internal_due_at: datetime | None
    official_due_at: datetime | None
    requirements: list[DeliverableRequirement]
    readiness: DeliverableReadiness
    latest_version: DeliverableVersionResponse | None = None
    latest_submission: SubmissionResponse | None = None
    workflow: WorkflowInstanceResponse | None = None
    created_at: datetime
    updated_at: datetime
    version: int
