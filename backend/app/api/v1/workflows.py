"""Generic governed-workflow configuration and transition endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionVersionCreate,
    WorkflowInstanceCreate,
    WorkflowTransitionRequest,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.workflow import WorkflowService

router = APIRouter(tags=["Workflows"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client is not None else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/workspaces/{workspace_id}/workflow-definitions", status_code=status.HTTP_201_CREATED)
async def create_workflow_definition(
    workspace_id: UUID,
    payload: WorkflowDefinitionCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await WorkflowService(session, actor).create_definition(
        workspace_id, payload, _audit_context(request)
    )
    return success_envelope(result.model_dump(mode="json"))


@router.post("/workflow-definition-versions/{version_id}/publish")
async def publish_workflow_definition_version(
    version_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await WorkflowService(session, actor).publish_version(
        version_id, audit=_audit_context(request)
    )
    return success_envelope(result.model_dump(mode="json"))


@router.post("/workflow-definitions/{definition_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_workflow_definition_version(
    definition_id: UUID,
    payload: WorkflowDefinitionVersionCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await WorkflowService(session, actor).create_definition_version(
        definition_id, payload, _audit_context(request)
    )
    return success_envelope(result.model_dump(mode="json"))


@router.post("/workspaces/{workspace_id}/workflow-instances", status_code=status.HTTP_201_CREATED)
async def start_workflow_instance(
    workspace_id: UUID,
    payload: WorkflowInstanceCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await WorkflowService(session, actor).start_instance(
        workspace_id, payload, _audit_context(request)
    )
    return success_envelope(result.model_dump(mode="json"))


@router.get("/workflow-instances/{instance_id}")
async def get_workflow_instance(
    instance_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await WorkflowService(session, actor).get_instance(instance_id)
    return success_envelope(result.model_dump(mode="json"))


@router.get("/workflow-instances/{instance_id}/history")
async def get_workflow_transition_history(
    instance_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, object]:
    result = await WorkflowService(session, actor).transition_history(
        instance_id, page=page, page_size=page_size
    )
    return success_envelope(result.model_dump(mode="json"))


@router.post("/workflow-instances/{instance_id}/actions/{action_key}")
async def transition_workflow_instance(
    instance_id: UUID,
    action_key: str,
    payload: WorkflowTransitionRequest,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await WorkflowService(session, actor).transition_instance(
        instance_id, action_key, payload, _audit_context(request)
    )
    return success_envelope(result.model_dump(mode="json"))
