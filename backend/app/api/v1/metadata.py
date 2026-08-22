"""Generic metadata administration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.metadata import (
    EntityTypeCreate,
    EntityTypeListResponse,
    EntityTypeResponse,
    EntityTypeUpdate,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.metadata import MetadataService

router = APIRouter(tags=["Metadata"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/workspaces/{workspace_id}/entity-types", status_code=status.HTTP_201_CREATED)
async def create_entity_type(
    workspace_id: UUID,
    payload: EntityTypeCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    entity_type = await MetadataService(session, actor).create_entity_type(
        workspace_id,
        values=payload.model_dump(),
        audit=_audit_context(request),
    )
    return success_envelope(EntityTypeResponse.model_validate(entity_type).model_dump(mode="json"))


@router.get("/workspaces/{workspace_id}/entity-types")
async def list_entity_types(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    active: bool | None = None,
    search: Annotated[str | None, Query(min_length=1, max_length=180)] = None,
) -> dict[str, object]:
    items, total = await MetadataService(session, actor).list_entity_types(
        workspace_id,
        page=page,
        page_size=page_size,
        active=active,
        search=search.strip() if search else None,
    )
    response = EntityTypeListResponse(
        items=tuple(EntityTypeResponse.model_validate(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))


@router.get("/entity-types/{entity_type_id}")
async def get_entity_type(
    entity_type_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    entity_type = await MetadataService(session, actor).get_entity_type(entity_type_id)
    return success_envelope(EntityTypeResponse.model_validate(entity_type).model_dump(mode="json"))


@router.patch("/entity-types/{entity_type_id}")
async def update_entity_type(
    entity_type_id: UUID,
    payload: EntityTypeUpdate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    entity_type = await MetadataService(session, actor).update_entity_type(
        entity_type_id,
        expected_version=payload.version,
        values=payload.model_dump(exclude={"version"}, exclude_unset=True),
        audit=_audit_context(request),
    )
    return success_envelope(EntityTypeResponse.model_validate(entity_type).model_dump(mode="json"))


@router.delete("/entity-types/{entity_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_entity_type(
    entity_type_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    version: Annotated[int, Query(ge=1)],
) -> None:
    await MetadataService(session, actor).archive_entity_type(
        entity_type_id,
        expected_version=version,
        audit=_audit_context(request),
    )
