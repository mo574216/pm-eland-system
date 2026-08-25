"""Workspace dashboard projection endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.envelopes import success_envelope
from app.core.database import get_database_session
from app.services.auth import AuthenticatedIdentity
from app.services.dashboard import DashboardService

router = APIRouter(tags=["Dashboards"])


@router.get("/workspaces/{workspace_id}/dashboard-summary")
async def get_dashboard_summary(
    workspace_id: UUID,
    actor: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    result = await DashboardService(session, actor).summary(workspace_id)
    return success_envelope(result.model_dump())
