"""Read-only workspace audit history endpoint."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.services.audit import AuditService
from app.services.auth import AuthenticatedIdentity

router = APIRouter(tags=["Audit"])


@router.get("/workspaces/{workspace_id}/audit")
async def get_workspace_audit_history(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    resource_type: Annotated[str | None, Query(max_length=100)] = None,
    resource_id: UUID | None = None,
    user_id: UUID | None = None,
    action: Annotated[str | None, Query(max_length=80)] = None,
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
) -> dict[str, object]:
    result = await AuditService(session, actor).history(
        workspace_id,
        page=page,
        page_size=page_size,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        action=action,
        from_at=from_at,
        to_at=to_at,
    )
    return success_envelope(result.model_dump())
