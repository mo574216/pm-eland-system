"""Generic governed-workflow API contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.permissions import PermissionCode
from app.schemas.metadata import STABLE_KEY_PATTERN

TargetKind = Literal["ENTITY", "DOCUMENT", "FORM_INSTANCE", "PHASE", "DELIVERABLE"]


class WorkflowStateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    label: str = Field(min_length=1, max_length=255)
    sequence_number: int = Field(ge=1)
    is_initial: bool = False
    is_terminal: bool = False


class WorkflowTransitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    key: str = Field(min_length=1, max_length=120, pattern=STABLE_KEY_PATTERN)
    label: str = Field(min_length=1, max_length=255)
    from_state_key: str = Field(pattern=STABLE_KEY_PATTERN)
    to_state_key: str = Field(pattern=STABLE_KEY_PATTERN)
    required_permission: PermissionCode
    authority_kind: str = Field(min_length=1, max_length=80, pattern=r"^[A-Z][A-Z0-9_]*$")
    assignment_kind: str | None = Field(default=None, max_length=80, pattern=r"^[A-Z][A-Z0-9_]*$")
    reason_required: bool = False


class WorkflowDefinitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    key: str | None = Field(default=None, max_length=120, pattern=STABLE_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    states: list[WorkflowStateCreate] = Field(min_length=2, max_length=50)
    transitions: list[WorkflowTransitionCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_graph(self) -> "WorkflowDefinitionCreate":
        state_keys = [state.key for state in self.states]
        if len(state_keys) != len(set(state_keys)):
            raise ValueError("State keys must be unique.")
        if sum(state.is_initial for state in self.states) != 1:
            raise ValueError("Exactly one initial state is required.")
        transition_keys = [transition.key for transition in self.transitions]
        if len(transition_keys) != len(set(transition_keys)):
            raise ValueError("Transition keys must be unique.")
        known = set(state_keys)
        if any(
            transition.from_state_key not in known or transition.to_state_key not in known
            for transition in self.transitions
        ):
            raise ValueError("Transitions must reference states in the same definition.")
        return self


class WorkflowDefinitionVersionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=1)
    states: list[WorkflowStateCreate] = Field(min_length=2, max_length=50)
    transitions: list[WorkflowTransitionCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_graph(self) -> "WorkflowDefinitionVersionCreate":
        state_keys = [state.key for state in self.states]
        transition_keys = [transition.key for transition in self.transitions]
        if len(state_keys) != len(set(state_keys)) or len(transition_keys) != len(
            set(transition_keys)
        ):
            raise ValueError("State and transition keys must be unique in their collections.")
        if sum(state.is_initial for state in self.states) != 1:
            raise ValueError("Exactly one initial state is required.")
        known = set(state_keys)
        if any(
            transition.from_state_key not in known or transition.to_state_key not in known
            for transition in self.transitions
        ):
            raise ValueError("Transitions must reference states in the same definition.")
        return self


class WorkflowAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    user_id: UUID
    assignment_kind: str = Field(min_length=1, max_length=80, pattern=r"^[A-Z][A-Z0-9_]*$")


class WorkflowInstanceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    definition_version_id: UUID
    target_kind: TargetKind
    target_id: UUID
    target_version: int | None = Field(default=None, ge=1)
    assignments: list[WorkflowAssignmentCreate] = Field(default_factory=list, max_length=100)
    idempotency_key: str = Field(min_length=8, max_length=255)


class WorkflowTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    expected_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=8, max_length=255)
    reason: str | None = Field(default=None, max_length=4000)
    target_version: int | None = Field(default=None, ge=1)


class WorkflowDefinitionResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    key: str
    name: str
    description: str | None
    version: int
    definition_version_id: UUID
    definition_version_number: int
    status: str


class WorkflowActionResponse(BaseModel):
    key: str
    label: str
    authority_kind: str
    reason_required: bool


class WorkflowInstanceResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    definition_version_id: UUID
    definition_version_number: int
    target_kind: str
    target_id: UUID
    target_version: int | None
    current_state_key: str
    current_state_label: str
    version: int
    available_actions: list[WorkflowActionResponse]


class WorkflowTransitionEventResponse(BaseModel):
    id: UUID
    action_key: str
    authority_kind: str
    previous_state_key: str | None
    resulting_state_key: str
    actor_id: UUID | None
    target_version: int | None
    resulting_instance_version: int
    reason: str | None
    occurred_at: datetime


class WorkflowTransitionHistoryResponse(BaseModel):
    items: list[WorkflowTransitionEventResponse]
    page: int
    page_size: int
    total: int
