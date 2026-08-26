"""Workflow transition permission, assignment, concurrency, and event tests."""

from contextlib import AbstractAsyncContextManager
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, ResourceConflictError, ResourceNotFoundError
from app.core.permissions import PermissionCode
from app.models.identity import User
from app.models.workflow import (
    WorkflowDefinitionVersion,
    WorkflowInstance,
    WorkflowStateDefinition,
    WorkflowTransitionDefinition,
    WorkflowTransitionEvent,
)
from app.models.workspace import Workspace
from app.repositories.workflow import WorkflowRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workflow import WorkflowTransitionRequest
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.workflow import WorkflowService


class Transaction(AbstractAsyncContextManager[None]):
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class Session:
    def begin(self) -> Transaction:
        return Transaction()

    def begin_nested(self) -> Transaction:
        return Transaction()

    def in_transaction(self) -> bool:
        return False


class WorkspaceRepo:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def accessible_workspace(self, *_: object) -> Workspace:
        return self.workspace

    async def workspace_permission_codes(self, *_: object) -> tuple[str, ...]:
        return ()


class Repo:
    def __init__(
        self, instance: WorkflowInstance, transition: WorkflowTransitionDefinition
    ) -> None:
        self.instance = instance
        self.transition_record = transition
        self.assignment = True
        self.accessible = True
        self.existing_event: WorkflowTransitionEvent | None = None
        self.package_ready = True
        self.added: list[object] = []
        self.previous = WorkflowStateDefinition(
            id=instance.current_state_id,
            workspace_id=instance.workspace_id,
            definition_version_id=instance.definition_version_id,
            key="draft",
            label="پیش‌نویس",
            sequence_number=1,
            is_initial=True,
            is_terminal=False,
            configuration={},
        )
        self.resulting = WorkflowStateDefinition(
            id=transition.to_state_id,
            workspace_id=instance.workspace_id,
            definition_version_id=instance.definition_version_id,
            key="submitted",
            label="ارسال‌شده",
            sequence_number=2,
            is_initial=False,
            is_terminal=False,
            configuration={},
        )

    async def accessible_instance(self, *_: object, **__: object) -> WorkflowInstance | None:
        return self.instance if self.accessible else None

    async def event_by_idempotency(self, *_: object) -> WorkflowTransitionEvent | None:
        return self.existing_event

    async def transition(self, *_: object) -> WorkflowTransitionDefinition:
        return self.transition_record

    async def has_assignment(self, *_: object) -> bool:
        return self.assignment

    async def deliverable_package_is_ready(self, *_: object) -> bool:
        return self.package_ready

    async def has_active_submission_version(self, *_: object) -> bool:
        return True

    async def latest_submission_is_withdrawn(self, *_: object) -> bool:
        return True

    async def state(self, state_id: UUID) -> WorkflowStateDefinition:
        return self.previous if state_id == self.previous.id else self.resulting

    async def version(self, _: UUID) -> WorkflowDefinitionVersion:
        return WorkflowDefinitionVersion(
            id=self.instance.definition_version_id,
            workspace_id=self.instance.workspace_id,
            definition_id=uuid4(),
            version_number=3,
            status="PUBLISHED",
            configuration={},
        )

    async def update_instance_state(
        self, _: UUID, expected_version: int, state_id: UUID, target_version: int | None
    ) -> WorkflowInstance:
        self.instance.current_state_id = state_id
        self.instance.version = expected_version + 1
        self.instance.target_version = target_version
        return self.instance

    async def transitions_from(self, *_: object) -> tuple[WorkflowTransitionDefinition, ...]:
        return ()

    def add(self, value: object) -> None:
        self.added.append(value)

    def add_audit_log(self, value: object) -> None:
        self.added.append(value)


def service(*permissions: PermissionCode) -> tuple[WorkflowService, Repo]:
    user = User(id=uuid4(), username="actor", email="actor@example.test", password_hash="unused")  # noqa: S106
    identity = AuthenticatedIdentity(
        user=user,
        roles=("CUSTOM",),
        permissions=tuple(permission.value for permission in permissions),
    )
    workspace = Workspace(id=uuid4(), name="A", slug="a", owner_id=user.id)
    instance = WorkflowInstance(
        id=uuid4(),
        workspace_id=workspace.id,
        definition_version_id=uuid4(),
        current_state_id=uuid4(),
        target_kind="PHASE",
        target_id=uuid4(),
        target_version=1,
        started_by=user.id,
        version=1,
    )
    transition = WorkflowTransitionDefinition(
        id=uuid4(),
        workspace_id=workspace.id,
        definition_version_id=instance.definition_version_id,
        key="submit",
        label="ارسال رسمی",
        from_state_id=instance.current_state_id,
        to_state_id=uuid4(),
        required_permission="SUBMISSION_CREATE",
        authority_kind="FORMAL_SUBMISSION",
        assignment_kind="SUBMITTER",
        reason_required=True,
        policy={},
    )
    result = WorkflowService(cast(AsyncSession, Session()), identity)
    repo = Repo(instance, transition)
    result.repository = cast(WorkflowRepository, repo)
    result.workspace_repository = cast(WorkspaceRepository, WorkspaceRepo(workspace))
    return result, repo


def request() -> WorkflowTransitionRequest:
    return WorkflowTransitionRequest(
        expected_version=1, idempotency_key="submission-001", reason="آماده ارسال", target_version=2
    )


@pytest.mark.asyncio
async def test_transition_requires_distinct_permission_and_assignment() -> None:
    result, _repo = service()
    with pytest.raises(PermissionDeniedError):
        await result.transition_instance(
            uuid4(), "submit", request(), AuditContext(uuid4(), None, None)
        )


@pytest.mark.asyncio
async def test_transition_enforces_configured_deliverable_readiness_policy() -> None:
    result, repo = service(PermissionCode.SUBMISSION_CREATE)
    repo.instance.target_kind = "DELIVERABLE"
    repo.transition_record.policy = {"requires_package_readiness": True}
    repo.package_ready = False

    with pytest.raises(ResourceConflictError):
        await result.transition_instance(
            repo.instance.id,
            "submit",
            request(),
            AuditContext(uuid4(), None, None),
        )

    result, repo = service(PermissionCode.SUBMISSION_CREATE)
    repo.assignment = False
    with pytest.raises(PermissionDeniedError):
        await result.transition_instance(
            uuid4(), "submit", request(), AuditContext(uuid4(), None, None)
        )


@pytest.mark.asyncio
async def test_transition_records_version_bound_event_and_audit() -> None:
    result, repo = service(PermissionCode.SUBMISSION_CREATE)
    response = await result.transition_instance(
        repo.instance.id, "submit", request(), AuditContext(uuid4(), None, None)
    )
    assert response.current_state_key == "submitted"
    assert response.definition_version_number == 3
    assert response.version == 2
    event = next(value for value in repo.added if isinstance(value, WorkflowTransitionEvent))
    assert event.definition_version_id == repo.instance.definition_version_id
    assert event.target_version == 2
    assert event.resulting_instance_version == 2
    assert event.authority_kind == "FORMAL_SUBMISSION"


@pytest.mark.asyncio
async def test_transition_hides_inaccessible_instance_and_is_idempotent() -> None:
    result, repo = service(PermissionCode.SUBMISSION_CREATE)
    repo.accessible = False
    with pytest.raises(ResourceNotFoundError):
        await result.transition_instance(
            repo.instance.id, "submit", request(), AuditContext(uuid4(), None, None)
        )

    result, repo = service(PermissionCode.SUBMISSION_CREATE)
    repo.existing_event = WorkflowTransitionEvent(
        id=uuid4(),
        workspace_id=repo.instance.workspace_id,
        instance_id=repo.instance.id,
        transition_id=repo.transition_record.id,
        definition_version_id=repo.instance.definition_version_id,
        previous_state_id=repo.previous.id,
        resulting_state_id=repo.resulting.id,
        action_key="submit",
        authority_kind="FORMAL_SUBMISSION",
        actor_id=uuid4(),
        target_version=2,
        resulting_instance_version=2,
        reason="آماده ارسال",
        context={},
        idempotency_key="submission-001",
    )
    response = await result.transition_instance(
        repo.instance.id, "submit", request(), AuditContext(uuid4(), None, None)
    )
    assert response.version == 1
    assert not repo.added

    with pytest.raises(ResourceConflictError):
        await result.transition_instance(
            repo.instance.id, "withdraw", request(), AuditContext(uuid4(), None, None)
        )
