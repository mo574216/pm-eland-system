"""Draft metadata-driven form definition endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.repositories.form import FormRecord
from app.schemas.form import (
    FormCreate,
    FormDefinitionResponse,
    FormFieldCreate,
    FormFieldResponse,
    FormLifecycleStatus,
    FormListResponse,
    FormRenderResponse,
    FormSummaryResponse,
    FormUpdate,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.form import FormService

router = APIRouter(tags=["Forms"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _form_response(record: FormRecord) -> FormDefinitionResponse:
    summary = FormSummaryResponse.model_validate(record.form)
    return FormDefinitionResponse(
        **summary.model_dump(),
        schema_definition=record.form.schema_json,
        fields=tuple(FormFieldResponse.model_validate(field) for field in record.fields),
    )


@router.post("/workspaces/{workspace_id}/forms", status_code=status.HTTP_201_CREATED)
async def create_form(
    workspace_id: UUID,
    payload: FormCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await FormService(session, actor).create_form(
        workspace_id, values=payload.model_dump(), audit=_audit_context(request)
    )
    return success_envelope(_form_response(record).model_dump(mode="json", by_alias=True))


@router.get("/workspaces/{workspace_id}/forms")
async def list_forms(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    entity_type_id: UUID | None = None,
    lifecycle_status: Annotated[FormLifecycleStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    items, total = await FormService(session, actor).list_forms(
        workspace_id,
        entity_type_id=entity_type_id,
        lifecycle_status=lifecycle_status,
        search=search.strip() if search else None,
        page=page,
        page_size=page_size,
    )
    response = FormListResponse(
        items=tuple(FormSummaryResponse.model_validate(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))


@router.get("/forms/{form_id}")
async def get_form(
    form_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await FormService(session, actor).get_form(form_id)
    return success_envelope(_form_response(record).model_dump(mode="json", by_alias=True))


@router.get("/forms/{form_id}/render")
async def render_form(
    form_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    entity_id: UUID | None = None,
) -> dict[str, object]:
    response: FormRenderResponse = await FormService(session, actor).render_form(
        form_id, entity_id=entity_id
    )
    return success_envelope(response.model_dump(mode="json"))


@router.patch("/forms/{form_id}")
async def update_form(
    form_id: UUID,
    payload: FormUpdate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await FormService(session, actor).update_draft_form(
        form_id,
        values=payload.model_dump(exclude_unset=True, by_alias=True),
        audit=_audit_context(request),
    )
    return success_envelope(_form_response(record).model_dump(mode="json", by_alias=True))


@router.post("/forms/{form_id}/fields", status_code=status.HTTP_201_CREATED)
async def add_form_field(
    form_id: UUID,
    payload: FormFieldCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    field = await FormService(session, actor).add_field(
        form_id, values=payload.model_dump(), audit=_audit_context(request)
    )
    return success_envelope(FormFieldResponse.model_validate(field).model_dump(mode="json"))


@router.post("/forms/{form_id}/publish")
async def publish_form(
    form_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await FormService(session, actor).publish_form(form_id, audit=_audit_context(request))
    return success_envelope(_form_response(record).model_dump(mode="json", by_alias=True))


@router.post("/forms/{form_id}/new-version", status_code=status.HTTP_201_CREATED)
async def create_new_form_version(
    form_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    record = await FormService(session, actor).create_new_version(
        form_id, audit=_audit_context(request)
    )
    return success_envelope(_form_response(record).model_dump(mode="json", by_alias=True))
