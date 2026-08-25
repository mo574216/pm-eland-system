"""Workspace-scoped, read-only audit history queries."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog, User


@dataclass(frozen=True)
class AuditEntryRecord:
    log: AuditLog
    username: str | None
    display_name: str | None


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_workspace_history(
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
    ) -> tuple[tuple[AuditEntryRecord, ...], int]:
        filters = [AuditLog.workspace_id == workspace_id]
        if resource_type is not None:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditLog.resource_id == resource_id)
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        if action is not None:
            filters.append(AuditLog.action == action)
        if from_at is not None:
            filters.append(AuditLog.created_at >= from_at)
        if to_at is not None:
            filters.append(AuditLog.created_at <= to_at)
        statement = (
            select(AuditLog, User.username, User.display_name)
            .outerjoin(User, User.id == AuditLog.user_id)
            .where(*filters)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await self.session.execute(statement)).all()
        total = int(
            (await self.session.scalar(select(func.count(AuditLog.id)).where(*filters))) or 0
        )
        return (
            tuple(
                AuditEntryRecord(log, username, display_name)
                for log, username, display_name in rows
            ),
            total,
        )
