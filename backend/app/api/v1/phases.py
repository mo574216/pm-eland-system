"""Workspace phase lifecycle and lock endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.phase import PhaseCreate, PhaseResponse, PhaseUpdate
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.phase import PhaseService

router = APIRouter(tags=["Phases"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _response(value: object) -> dict[str, object]:
    return PhaseResponse.model_validate(value).model_dump(mode="json")


@router.post("/workspaces/{workspace_id}/phases", status_code=status.HTTP_201_CREATED)
async def create_phase(
    workspace_id: UUID,
    payload: PhaseCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await PhaseService(session, actor).create_phase(
        workspace_id, values=payload.model_dump(), audit=_audit_context(request)
    )
    return success_envelope(_response(value))


@router.get("/workspaces/{workspace_id}/phases")
async def list_phases(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    values = await PhaseService(session, actor).list_phases(workspace_id)
    return success_envelope([_response(value) for value in values])


@router.patch("/phases/{phase_id}")
async def update_phase(
    phase_id: UUID,
    payload: PhaseUpdate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await PhaseService(session, actor).update_phase(
        phase_id,
        expected_version=payload.version,
        values=payload.model_dump(exclude={"version"}, exclude_unset=True),
        audit=_audit_context(request),
    )
    return success_envelope(_response(value))


@router.post("/phases/{phase_id}/lock")
async def lock_phase(
    phase_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await PhaseService(session, actor).set_locked(
        phase_id, locked=True, audit=_audit_context(request)
    )
    return success_envelope(_response(value))


@router.post("/phases/{phase_id}/unlock")
async def unlock_phase(
    phase_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await PhaseService(session, actor).set_locked(
        phase_id, locked=False, audit=_audit_context(request)
    )
    return success_envelope(_response(value))
