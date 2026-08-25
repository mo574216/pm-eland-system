"""Safe allowlisted aggregate queries for workspace dashboards."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.entity import EntityObject
from app.models.phase import Phase, PhaseDeliverable


class DashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary_counts(self, workspace_id: UUID) -> tuple[int, int, int, int, int, int]:
        queries = (
            select(func.count(EntityObject.id)).where(
                EntityObject.workspace_id == workspace_id,
                EntityObject.deleted_at.is_(None),
                EntityObject.status == "ACTIVE",
            ),
            select(func.count(Document.id)).where(
                Document.workspace_id == workspace_id,
                Document.deleted_at.is_(None),
                Document.lifecycle_status == "ACTIVE",
            ),
            select(func.count(Phase.id)).where(
                Phase.workspace_id == workspace_id, Phase.status != "ARCHIVED"
            ),
            select(func.count(Phase.id)).where(
                Phase.workspace_id == workspace_id, Phase.status == "COMPLETED"
            ),
            select(func.count(PhaseDeliverable.id))
            .join(Phase)
            .where(Phase.workspace_id == workspace_id, PhaseDeliverable.status != "APPROVED"),
            select(func.count(PhaseDeliverable.id))
            .join(Phase)
            .where(Phase.workspace_id == workspace_id, PhaseDeliverable.status == "APPROVED"),
        )
        values: list[int] = []
        for query in queries:
            values.append(int((await self.session.scalar(query)) or 0))
        return (values[0], values[1], values[2], values[3], values[4], values[5])
