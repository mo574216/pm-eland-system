"""Authorization-bound audit history service."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError, WorkspaceAccessDeniedError
from app.core.permissions import PermissionCode
from app.repositories.audit import AuditRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.audit import AuditEntryResponse, AuditHistoryResponse
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuthorizationService


class AuditService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = AuditRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

    async def history(
        self,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
        resource_type: str | None,
        resource_id: UUID | None,
        user_id: UUID | None,
        action: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
    ) -> AuditHistoryResponse:
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
        if PermissionCode.AUDIT_READ.value not in effective:
            raise PermissionDeniedError
        records, total = await self.repository.list_workspace_history(
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
        return AuditHistoryResponse(
            items=[
                AuditEntryResponse(
                    id=record.log.id,
                    action=record.log.action,
                    resource_type=record.log.resource_type,
                    resource_id=record.log.resource_id,
                    source=record.log.source,
                    actor_name=record.display_name or record.username or "System",
                    before_state=record.log.before_state,
                    after_state=record.log.after_state,
                    created_at=record.log.created_at,
                )
                for record in records
            ],
            total=total,
            page=page,
            page_size=page_size,
        )
