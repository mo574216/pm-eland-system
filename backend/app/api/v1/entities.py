"""Generic entity-object endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.repositories.entity import EntityRecord
from app.schemas.entity import (
    EntityCreate,
    EntityListResponse,
    EntityResponse,
    EntityTypeSummary,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.entity import EntityService

router = APIRouter(tags=["Entities"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _entity_response(record: EntityRecord) -> EntityResponse:
    entity = record.entity
    return EntityResponse(
        id=entity.id,
        workspace_id=entity.workspace_id,
        entity_type_id=entity.entity_type_id,
        entity_type=EntityTypeSummary.model_validate(record.entity_type),
        parent_id=entity.parent_id,
        name=entity.name,
        description=entity.description,
        status=entity.status,
        attributes=entity.attributes,
        created_by=entity.created_by,
        updated_by=entity.updated_by,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        archived_at=entity.archived_at,
        version=entity.version,
    )


@router.post("/workspaces/{workspace_id}/entities", status_code=status.HTTP_201_CREATED)
async def create_entity(
    workspace_id: UUID,
    payload: EntityCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    entity = await EntityService(session, actor).create_entity(
        workspace_id,
        entity_type_id=payload.entity_type_id,
        parent_id=payload.parent_id,
        name=payload.name,
        description=payload.description,
        attributes=payload.attributes,
        audit=_audit_context(request),
    )
    return success_envelope(_entity_response(entity).model_dump(mode="json"))


@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    entity = await EntityService(session, actor).get_entity(entity_id)
    return success_envelope(_entity_response(entity).model_dump(mode="json"))


@router.get("/workspaces/{workspace_id}/entities")
async def list_entities(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    entity_status: Annotated[
        str | None, Query(alias="status", pattern="^(ACTIVE|ARCHIVED)$")
    ] = None,
    entity_type_id: UUID | None = None,
    parent_id: UUID | None = None,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
) -> dict[str, object]:
    items, total = await EntityService(session, actor).list_entities(
        workspace_id,
        page=page,
        page_size=page_size,
        status=entity_status,
        entity_type_id=entity_type_id,
        parent_id=parent_id,
        search=search,
    )
    response = EntityListResponse(
        items=tuple(_entity_response(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))
