"""Metadata-defined relationship endpoints."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.request_context import get_request_id
from app.schemas.relationship import (
    RelationshipCreate,
    RelationshipListResponse,
    RelationshipResponse,
    RelationshipTypeCreate,
    RelationshipTypeListResponse,
    RelationshipTypeResponse,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.relationship import RelationshipService

router = APIRouter(tags=["Relationships"])


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post(
    "/workspaces/{workspace_id}/relationship-types",
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship_type(
    workspace_id: UUID,
    payload: RelationshipTypeCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await RelationshipService(session, actor).create_relationship_type(
        workspace_id, values=payload.model_dump(), audit=_audit_context(request)
    )
    return success_envelope(RelationshipTypeResponse.model_validate(value).model_dump(mode="json"))


@router.get("/workspaces/{workspace_id}/relationship-types")
async def list_relationship_types(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    items, total = await RelationshipService(session, actor).list_relationship_types(
        workspace_id, page=page, page_size=page_size
    )
    response = RelationshipTypeListResponse(
        items=tuple(RelationshipTypeResponse.model_validate(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))


@router.post(
    "/workspaces/{workspace_id}/relationships",
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship(
    workspace_id: UUID,
    payload: RelationshipCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    value = await RelationshipService(session, actor).create_relationship(
        workspace_id, **payload.model_dump(), audit=_audit_context(request)
    )
    return success_envelope(RelationshipResponse.model_validate(value).model_dump(mode="json"))


@router.get("/entities/{entity_id}/relationships")
async def list_relationships(
    entity_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    direction: Literal["incoming", "outgoing", "both"] = "both",
    relationship_type_id: UUID | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, object]:
    items, total = await RelationshipService(session, actor).list_relationships(
        entity_id,
        direction=direction,
        relationship_type_id=relationship_type_id,
        page=page,
        page_size=page_size,
    )
    response = RelationshipListResponse(
        items=tuple(RelationshipResponse.model_validate(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(response.model_dump(mode="json"))


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await RelationshipService(session, actor).delete_relationship(
        relationship_id, audit=_audit_context(request)
    )
