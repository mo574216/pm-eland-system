"""Phase-context deliverable and formal submission endpoints."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.deliverable import (
    DeliverableCreate,
    DeliverableVersionCreate,
    SubmissionCreate,
    SubmissionWithdrawalCreate,
)
from app.schemas.workflow import WorkflowTransitionRequest
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.deliverable import DeliverableService

router = APIRouter(tags=["Deliverables"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client is not None else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/phases/{phase_id}/deliverables", status_code=status.HTTP_201_CREATED)
async def create_deliverable(
    phase_id: UUID,
    payload: DeliverableCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await DeliverableService(session, actor).create(
        phase_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.get("/phases/{phase_id}/deliverables")
async def list_deliverables(
    phase_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    values = await DeliverableService(session, actor).list_for_phase(phase_id)
    return success_envelope([value.model_dump(mode="json") for value in values])


@router.get("/deliverables/{deliverable_id}")
async def get_deliverable(
    deliverable_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await DeliverableService(session, actor).get(deliverable_id)
    return success_envelope(value.model_dump(mode="json"))


@router.get("/deliverables/{deliverable_id}/package-options")
async def list_package_options(
    deliverable_id: UUID,
    kind: Annotated[
        Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"],
        Query(),
    ],
    search: Annotated[str, Query(min_length=2, max_length=120)],
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> dict[str, object]:
    values = await DeliverableService(session, actor).package_options(
        deliverable_id, kind, search, limit
    )
    return success_envelope([value.model_dump(mode="json") for value in values])


@router.post("/deliverables/{deliverable_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_deliverable_version(
    deliverable_id: UUID,
    payload: DeliverableVersionCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await DeliverableService(session, actor).create_version(
        deliverable_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.post("/deliverables/{deliverable_id}/actions/{action_key}")
async def transition_deliverable_review(
    deliverable_id: UUID,
    action_key: str,
    payload: WorkflowTransitionRequest,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await DeliverableService(session, actor).transition_review(
        deliverable_id, action_key, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.post("/deliverables/{deliverable_id}/submissions", status_code=status.HTTP_201_CREATED)
async def create_submission(
    deliverable_id: UUID,
    payload: SubmissionCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await DeliverableService(session, actor).submit(
        deliverable_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.post("/submissions/{submission_id}/withdrawals", status_code=status.HTTP_201_CREATED)
async def withdraw_submission(
    submission_id: UUID,
    payload: SubmissionWithdrawalCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await DeliverableService(session, actor).withdraw(
        submission_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))
