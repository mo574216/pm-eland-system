"""Regression coverage for workspace-scoped workflow persistence ordering."""

from uuid import uuid4

import pytest

from app.core.deliverable_workflow import DELIVERABLE_TRANSITIONS
from app.models.deliverable import Deliverable, DeliverableAssignment
from app.models.identity import User
from app.models.workflow import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowDefinitionVersion,
    WorkflowInstance,
    WorkflowStateDefinition,
    WorkflowTransitionDefinition,
    WorkflowTransitionEvent,
)
from app.services.auth import AuthenticatedIdentity
from app.services.deliverable import DeliverableService


class WorkflowRepositoryRecorder:
    def __init__(self) -> None:
        self.operations: list[tuple[str, list[object]]] = []

    async def definition_by_key(self, *_: object) -> None:
        return None

    async def latest_published_version(self, *_: object) -> None:
        return None

    def add_all(self, values: list[object]) -> None:
        self.operations.append(("add", values))

    async def flush(self) -> None:
        self.operations.append(("flush", []))


def service() -> DeliverableService:
    user = User(
        id=uuid4(),
        username="manager",
        email="manager@example.test",
        password_hash="unused",  # noqa: S106
    )
    identity = AuthenticatedIdentity(user=user, roles=("PROJECT_MANAGER",), permissions=())
    return DeliverableService(None, identity)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_new_workflow_profile_flushes_each_composite_fk_dependency_layer() -> None:
    value = service()
    recorder = WorkflowRepositoryRecorder()
    value.workflow_repository = recorder  # type: ignore[assignment]

    await value._ensure_workflow_profile(uuid4())

    added_types = [
        [type(item) for item in batch]
        for action, batch in recorder.operations
        if action == "add"
    ]
    assert added_types == [
        [WorkflowDefinition],
        [WorkflowDefinitionVersion],
        [WorkflowStateDefinition] * 4,
        [WorkflowTransitionDefinition] * len(DELIVERABLE_TRANSITIONS),
    ]
    assert [action for action, _ in recorder.operations] == [
        "add", "flush", "add", "flush", "add", "flush", "add", "flush"
    ]


@pytest.mark.asyncio
async def test_workflow_instance_is_flushed_before_composite_fk_children() -> None:
    value = service()
    recorder = WorkflowRepositoryRecorder()
    value.workflow_repository = recorder  # type: ignore[assignment]
    workspace_id = uuid4()
    definition_version = WorkflowDefinitionVersion(
        id=uuid4(), workspace_id=workspace_id, definition_id=uuid4(), version_number=1,
        status="PUBLISHED", configuration={},
    )
    state = WorkflowStateDefinition(
        id=uuid4(), workspace_id=workspace_id, definition_version_id=definition_version.id,
        key="preparation", label="Preparation", sequence_number=1, is_initial=True,
        is_terminal=False, configuration={},
    )
    deliverable = Deliverable(
        id=uuid4(), workspace_id=workspace_id, phase_id=uuid4(), key="delivery_demo",
        name="Demo", description=None, owner_id=value.actor.user.id,
        internal_reviewer_id=None, requirements=[], created_by=value.actor.user.id, version=1,
    )
    assignment = DeliverableAssignment(
        id=uuid4(), workspace_id=workspace_id, deliverable_id=deliverable.id,
        user_id=value.actor.user.id, assignment_kind="OWNER", assigned_by=value.actor.user.id,
    )

    await value._create_workflow_instance(deliverable, definition_version, state, [assignment])

    assert [action for action, _ in recorder.operations] == ["add", "flush", "add"]
    assert isinstance(recorder.operations[0][1][0], WorkflowInstance)
    assert {type(item) for item in recorder.operations[2][1]} == {
        WorkflowAssignment,
        WorkflowTransitionEvent,
    }
