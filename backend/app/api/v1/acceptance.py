"""Phase acceptance package, decision, condition, and closure endpoints."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.acceptance import (
    AcceptanceClosureCreate,
    AcceptanceConditionEvidenceCreate,
    AcceptanceConditionVerificationCreate,
    AcceptanceDecisionCreate,
    AcceptancePackageCreate,
)
from app.services.acceptance import AcceptanceService
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext

router = APIRouter(tags=["Acceptance"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client is not None else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/phases/{phase_id}/acceptance-packages")
async def list_phase_acceptance_packages(
    phase_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    values = await AcceptanceService(session, actor).list_for_phase(phase_id)
    return success_envelope([value.model_dump(mode="json") for value in values])


@router.get("/phases/{phase_id}/acceptance-workspace")
async def get_phase_acceptance_workspace(
    phase_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await AcceptanceService(session, actor).workspace(phase_id)
    return success_envelope(value.model_dump(mode="json"))


@router.post("/phases/{phase_id}/acceptance-packages", status_code=status.HTTP_201_CREATED)
async def create_phase_acceptance_package(
    phase_id: UUID,
    payload: AcceptancePackageCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await AcceptanceService(session, actor).create_package(
        phase_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.post("/acceptance-packages/{package_id}/decisions", status_code=status.HTTP_201_CREATED)
async def create_acceptance_decision(
    package_id: UUID,
    payload: AcceptanceDecisionCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await AcceptanceService(session, actor).decide(
        package_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.post("/acceptance-conditions/{condition_id}/evidence", status_code=status.HTTP_201_CREATED)
async def submit_acceptance_condition_evidence(
    condition_id: UUID,
    payload: AcceptanceConditionEvidenceCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await AcceptanceService(session, actor).submit_condition_evidence(
        condition_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.get("/acceptance-conditions/{condition_id}/evidence-options")
async def list_acceptance_condition_evidence_options(
    condition_id: UUID,
    kind: Annotated[Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"], Query()],
    search: Annotated[str, Query(min_length=2, max_length=120)],
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> dict[str, object]:
    values = await AcceptanceService(session, actor).evidence_options(
        condition_id, kind, search, limit
    )
    return success_envelope([value.model_dump(mode="json") for value in values])


@router.post("/acceptance-conditions/{condition_id}/verification")
async def verify_acceptance_condition(
    condition_id: UUID,
    payload: AcceptanceConditionVerificationCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await AcceptanceService(session, actor).verify_condition(
        condition_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))


@router.post("/acceptance-decisions/{decision_id}/closure", status_code=status.HTTP_201_CREATED)
async def close_conditional_acceptance(
    decision_id: UUID,
    payload: AcceptanceClosureCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await AcceptanceService(session, actor).close_conditional_acceptance(
        decision_id, payload, _audit_context(request)
    )
    return success_envelope(value.model_dump(mode="json"))
