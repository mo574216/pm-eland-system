"""Authorization-bound server-defined dashboard projections."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, WorkspaceAccessDeniedError
from app.core.permissions import PermissionCode
from app.repositories.dashboard import DashboardRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.dashboard import DashboardSummaryResponse, DeliverableProgress, PhaseProgress
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuthorizationService


class DashboardService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = DashboardRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

    async def summary(self, workspace_id: UUID) -> DashboardSummaryResponse:
        if (
            await self.workspace_repository.accessible_workspace(workspace_id, self.actor.user.id)
            is None
        ):
            raise WorkspaceAccessDeniedError
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if PermissionCode.DASHBOARD_READ.value not in effective:
            raise PermissionDeniedError
        (
            entities,
            documents,
            phases,
            completed_phases,
            pending,
            completed,
        ) = await self.repository.summary_counts(workspace_id)
        percent = round(completed_phases * 100 / phases) if phases else 0
        return DashboardSummaryResponse(
            entity_count=entities,
            document_count=documents,
            phases=PhaseProgress(total=phases, completed=completed_phases, percent=percent),
            deliverables=DeliverableProgress(pending=pending, completed=completed),
        )
