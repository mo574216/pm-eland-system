"""Global user role administration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authorization import require_permission
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.core.permissions import PermissionCode
from app.core.request_context import get_request_id
from app.schemas.authorization import RoleAssignmentRequest, RoleAssignmentResponse
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, RoleAssignmentService

router = APIRouter(prefix="/users", tags=["Identity"])
identity_manager = require_permission(PermissionCode.IDENTITY_MANAGE)


def _audit_context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=UUID(get_request_id()),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/{user_id}/roles")
async def assign_role(
    user_id: UUID,
    payload: RoleAssignmentRequest,
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(identity_manager)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    role, changed = await RoleAssignmentService(session, actor).assign_role(
        user_id, payload.role_code, _audit_context(request)
    )
    data = RoleAssignmentResponse(role_code=role.code, changed=changed)
    return success_envelope(data.model_dump())


@router.delete("/{user_id}/roles/{role_code}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role(
    user_id: UUID,
    role_code: Annotated[str, Path(min_length=1, max_length=100, pattern=r"^[A-Z][A-Z0-9_]*$")],
    request: Request,
    actor: Annotated[AuthenticatedIdentity, Depends(identity_manager)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> None:
    await RoleAssignmentService(session, actor).remove_role(
        user_id, role_code, _audit_context(request)
    )
