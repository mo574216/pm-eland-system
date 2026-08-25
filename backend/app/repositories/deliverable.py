"""Workspace-isolated persistence for deliverables and submission evidence."""

from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deliverable import (
    Deliverable,
    DeliverableAssignment,
    DeliverablePackageItem,
    DeliverableVersion,
    Submission,
    SubmissionRecipient,
    SubmissionWithdrawal,
)
from app.models.identity import AuditLog
from app.models.workspace import WorkspaceMembership


class DeliverableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_all(self, values: list[object]) -> None:
        self.session.add_all(values)

    def add_audit_log(self, value: AuditLog) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def active_member_ids(self, workspace_id: UUID, ids: set[UUID]) -> set[UUID]:
        if not ids:
            return set()
        return set(
            (
                await self.session.scalars(
                    select(WorkspaceMembership.user_id).where(
                        WorkspaceMembership.workspace_id == workspace_id,
                        WorkspaceMembership.status == "ACTIVE",
                        WorkspaceMembership.user_id.in_(ids),
                    )
                )
            ).all()
        )

    async def accessible(
        self, deliverable_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> Deliverable | None:
        statement = (
            select(Deliverable)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Deliverable.workspace_id,
            )
            .where(
                Deliverable.id == deliverable_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update()
        return cast(Deliverable | None, await self.session.scalar(statement))

    async def list_for_phase(
        self, phase_id: UUID, workspace_id: UUID, user_id: UUID
    ) -> tuple[Deliverable, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(Deliverable)
                    .join(
                        WorkspaceMembership,
                        WorkspaceMembership.workspace_id == Deliverable.workspace_id,
                    )
                    .where(
                        Deliverable.phase_id == phase_id,
                        Deliverable.workspace_id == workspace_id,
                        WorkspaceMembership.user_id == user_id,
                        WorkspaceMembership.status == "ACTIVE",
                    )
                    .order_by(Deliverable.created_at, Deliverable.id)
                )
            ).all()
        )

    async def assignments(self, deliverable_id: UUID) -> tuple[DeliverableAssignment, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(DeliverableAssignment).where(
                        DeliverableAssignment.deliverable_id == deliverable_id
                    )
                )
            ).all()
        )

    async def latest_version(self, deliverable_id: UUID) -> DeliverableVersion | None:
        return cast(
            DeliverableVersion | None,
            await self.session.scalar(
                select(DeliverableVersion)
                .where(DeliverableVersion.deliverable_id == deliverable_id)
                .order_by(DeliverableVersion.version_number.desc())
                .limit(1)
            ),
        )

    async def version(self, deliverable_id: UUID, version_id: UUID) -> DeliverableVersion | None:
        return cast(
            DeliverableVersion | None,
            await self.session.scalar(
                select(DeliverableVersion).where(
                    DeliverableVersion.deliverable_id == deliverable_id,
                    DeliverableVersion.id == version_id,
                )
            ),
        )

    async def package_items(self, version_id: UUID) -> tuple[DeliverablePackageItem, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(DeliverablePackageItem).where(
                        DeliverablePackageItem.deliverable_version_id == version_id
                    )
                )
            ).all()
        )

    async def next_version_number(self, deliverable_id: UUID) -> int:
        value = await self.session.scalar(
            select(func.coalesce(func.max(DeliverableVersion.version_number), 0)).where(
                DeliverableVersion.deliverable_id == deliverable_id
            )
        )
        return int(value or 0) + 1

    async def latest_submission(self, deliverable_id: UUID) -> Submission | None:
        return cast(
            Submission | None,
            await self.session.scalar(
                select(Submission)
                .where(Submission.deliverable_id == deliverable_id)
                .order_by(Submission.sequence_number.desc())
                .limit(1)
            ),
        )

    async def submission_by_idempotency(self, deliverable_id: UUID, key: str) -> Submission | None:
        return cast(
            Submission | None,
            await self.session.scalar(
                select(Submission).where(
                    Submission.deliverable_id == deliverable_id,
                    Submission.idempotency_key == key,
                )
            ),
        )

    async def submission(self, submission_id: UUID, user_id: UUID) -> Submission | None:
        return cast(
            Submission | None,
            await self.session.scalar(
                select(Submission)
                .join(
                    WorkspaceMembership,
                    WorkspaceMembership.workspace_id == Submission.workspace_id,
                )
                .where(
                    Submission.id == submission_id,
                    WorkspaceMembership.user_id == user_id,
                    WorkspaceMembership.status == "ACTIVE",
                )
            ),
        )

    async def recipients(self, submission_id: UUID) -> tuple[SubmissionRecipient, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(SubmissionRecipient).where(
                        SubmissionRecipient.submission_id == submission_id
                    )
                )
            ).all()
        )

    async def latest_withdrawal(self, submission_id: UUID) -> SubmissionWithdrawal | None:
        return cast(
            SubmissionWithdrawal | None,
            await self.session.scalar(
                select(SubmissionWithdrawal)
                .where(SubmissionWithdrawal.submission_id == submission_id)
                .order_by(SubmissionWithdrawal.withdrawn_at.desc())
                .limit(1)
            ),
        )

    async def withdrawal_by_idempotency(
        self, submission_id: UUID, key: str
    ) -> SubmissionWithdrawal | None:
        return cast(
            SubmissionWithdrawal | None,
            await self.session.scalar(
                select(SubmissionWithdrawal).where(
                    SubmissionWithdrawal.submission_id == submission_id,
                    SubmissionWithdrawal.idempotency_key == key,
                )
            ),
        )
