"""Workspace-isolated phase persistence operations."""

from typing import cast
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog
from app.models.phase import Phase
from app.models.workspace import WorkspaceMembership


class PhaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_phase(self, value: Phase) -> None:
        self.session.add(value)

    def add_audit_log(self, value: AuditLog) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def by_key(self, workspace_id: UUID, key: str) -> Phase | None:
        return cast(
            Phase | None,
            await self.session.scalar(
                select(Phase).where(Phase.workspace_id == workspace_id, Phase.key == key)
            ),
        )

    async def accessible_phase(
        self, phase_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> Phase | None:
        statement = (
            select(Phase)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Phase.workspace_id)
            .where(
                Phase.id == phase_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update()
        return cast(Phase | None, await self.session.scalar(statement))

    async def list_phases(self, workspace_id: UUID, user_id: UUID) -> tuple[Phase, ...]:
        statement = (
            select(Phase)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Phase.workspace_id)
            .where(
                Phase.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
            .order_by(Phase.sequence_number, Phase.id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def update_phase(
        self, phase_id: UUID, expected_version: int, values: dict[str, object]
    ) -> Phase | None:
        statement = (
            update(Phase)
            .where(Phase.id == phase_id, Phase.version == expected_version)
            .values(**values, version=Phase.version + 1, updated_at=func.now())
            .returning(Phase)
        )
        return cast(Phase | None, await self.session.scalar(statement))

    async def set_lock(self, phase_id: UUID, *, locked: bool, actor_id: UUID) -> Phase | None:
        values: dict[str, object] = {
            "is_locked": locked,
            "locked_by": actor_id if locked else None,
            "locked_at": func.now() if locked else None,
            "updated_at": func.now(),
            "version": Phase.version + 1,
        }
        return cast(
            Phase | None,
            await self.session.scalar(
                update(Phase).where(Phase.id == phase_id).values(**values).returning(Phase)
            ),
        )
