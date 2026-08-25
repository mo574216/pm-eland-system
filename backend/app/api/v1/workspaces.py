"""Workspace lifecycle and membership endpoints."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.dependencies.authorization import require_permission
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.permissions import PermissionCode
from app.core.request_context import get_request_id
from app.repositories.workspace import WorkspaceMemberRecord
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspacePersonOptionResponse,
    WorkspaceResponse,
    WorkspaceRoleOptionResponse,
    WorkspaceUpdate,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])
workspace_creator = require_permission(PermissionCode.WORKSPACE_CREATE)


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def _member_response(record: WorkspaceMemberRecord) -> WorkspaceMemberResponse:
    return WorkspaceMemberResponse(
        id=record.membership.id,
        user_id=record.membership.user_id,
        username=record.username,
        display_name=record.display_name,
        role_id=record.membership.role_id,
        role_code=record.role_code,
        status=record.membership.status,
        created_at=record.membership.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(workspace_creator)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    workspace = await WorkspaceService(session, actor).create_workspace(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        audit=_audit_context(request),
    )
    return success_envelope(WorkspaceResponse.model_validate(workspace).model_dump(mode="json"))


@router.get("")
async def list_workspaces(
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    workspace_status: Annotated[
        Literal["DRAFT", "ACTIVE", "ARCHIVED"] | None, Query(alias="status")
    ] = None,
    search: Annotated[str | None, Query(min_length=1, max_length=255)] = None,
) -> dict[str, object]:
    items, total = await WorkspaceService(session, actor).list_workspaces(
        page=page,
        page_size=page_size,
        status=workspace_status,
        search=search.strip() if search else None,
    )
    data = WorkspaceListResponse(
        items=tuple(WorkspaceResponse.model_validate(item) for item in items),
        page=page,
        page_size=page_size,
        total=total,
    )
    return success_envelope(data.model_dump(mode="json"))


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    workspace = await WorkspaceService(session, actor).get_workspace(workspace_id)
    return success_envelope(WorkspaceResponse.model_validate(workspace).model_dump(mode="json"))


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    values = payload.model_dump(exclude={"version"}, exclude_unset=True)
    workspace = await WorkspaceService(session, actor).update_workspace(
        workspace_id,
        expected_version=payload.version,
        values=values,
        audit=_audit_context(request),
    )
    return success_envelope(WorkspaceResponse.model_validate(workspace).model_dump(mode="json"))


@router.get("/{workspace_id}/members")
async def list_workspace_members(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    members = await WorkspaceService(session, actor).list_members(workspace_id)
    return success_envelope(
        [_member_response(member).model_dump(mode="json") for member in members]
    )


@router.get("/{workspace_id}/member-options")
async def search_workspace_member_options(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    search: Annotated[str, Query(min_length=2, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> dict[str, object]:
    users = await WorkspaceService(session, actor).search_member_candidates(
        workspace_id, search=search.strip(), limit=limit
    )
    return success_envelope(
        [
            WorkspacePersonOptionResponse.model_validate(user, from_attributes=True).model_dump(
                mode="json"
            )
            for user in users
        ]
    )


@router.get("/{workspace_id}/role-options")
async def list_workspace_role_options(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    roles = await WorkspaceService(session, actor).list_assignable_roles(workspace_id)
    return success_envelope(
        [
            WorkspaceRoleOptionResponse.model_validate(role, from_attributes=True).model_dump(
                mode="json"
            )
            for role in roles
        ]
    )


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: UUID,
    payload: WorkspaceMemberCreate,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    member = await WorkspaceService(session, actor).add_member(
        workspace_id,
        user_id=payload.user_id,
        role_id=payload.role_id,
        audit=_audit_context(request),
    )
    return success_envelope(_member_response(member).model_dump(mode="json"))


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await WorkspaceService(session, actor).remove_member(
        workspace_id, user_id, _audit_context(request)
    )
