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
    ReviewComment,
    ReviewOutcome,
    Submission,
    SubmissionRecipient,
    SubmissionWithdrawal,
)
from app.models.identity import AuditLog, Permission, Role, User, role_permissions
from app.models.workspace import WorkspaceMembership


class DeliverableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_all(self, values: list[object]) -> None:
        self.session.add_all(values)

    async def assignment_options(
        self, workspace_id: UUID, permission_code: str
    ) -> tuple[tuple[UUID, str, str | None, str | None], ...]:
        rows = await self.session.execute(
            select(WorkspaceMembership.user_id, User.username, User.display_name, Role.code)
            .join(User, User.id == WorkspaceMembership.user_id)
            .join(Role, Role.id == WorkspaceMembership.role_id)
            .join(role_permissions, role_permissions.c.role_id == Role.id)
            .join(Permission, Permission.id == role_permissions.c.permission_id)
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.status == "ACTIVE",
                Permission.code == permission_code,
            )
            .order_by(User.display_name, User.username)
            .distinct()
        )
        return tuple((row[0], row[1], row[2], row[3]) for row in rows.all())

    async def review_comments(self, submission_id: UUID) -> tuple[ReviewComment, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(ReviewComment)
                    .where(ReviewComment.submission_id == submission_id)
                    .order_by(ReviewComment.created_at, ReviewComment.id)
                )
            ).all()
        )

    async def review_outcomes(self, submission_id: UUID) -> tuple[ReviewOutcome, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(ReviewOutcome)
                    .where(ReviewOutcome.submission_id == submission_id)
                    .order_by(ReviewOutcome.created_at, ReviewOutcome.id)
                )
            ).all()
        )

    async def review_comment_by_idempotency(
        self, submission_id: UUID, key: str
    ) -> ReviewComment | None:
        return cast(
            ReviewComment | None,
            await self.session.scalar(
                select(ReviewComment).where(
                    ReviewComment.submission_id == submission_id,
                    ReviewComment.idempotency_key == key,
                )
            ),
        )

    async def review_outcome_by_idempotency(
        self, submission_id: UUID, key: str
    ) -> ReviewOutcome | None:
        return cast(
            ReviewOutcome | None,
            await self.session.scalar(
                select(ReviewOutcome).where(
                    ReviewOutcome.submission_id == submission_id,
                    ReviewOutcome.idempotency_key == key,
                )
            ),
        )

    async def is_submission_recipient(self, submission_id: UUID, user_id: UUID) -> bool:
        return (
            await self.session.scalar(
                select(SubmissionRecipient.id).where(
                    SubmissionRecipient.submission_id == submission_id,
                    SubmissionRecipient.user_id == user_id,
                )
            )
            is not None
        )

    async def review_comments_by_ids(
        self, submission_id: UUID, comment_ids: set[UUID]
    ) -> set[UUID]:
        if not comment_ids:
            return set()
        return set(
            (
                await self.session.scalars(
                    select(ReviewComment.id).where(
                        ReviewComment.submission_id == submission_id,
                        ReviewComment.id.in_(comment_ids),
                    )
                )
            ).all()
        )

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

    async def active_member_ids_with_permission(
        self, workspace_id: UUID, ids: set[UUID], permission_code: str
    ) -> set[UUID]:
        if not ids:
            return set()
        return set(
            (
                await self.session.scalars(
                    select(WorkspaceMembership.user_id)
                    .join(Role, Role.id == WorkspaceMembership.role_id)
                    .join(role_permissions, role_permissions.c.role_id == Role.id)
                    .join(Permission, Permission.id == role_permissions.c.permission_id)
                    .where(
                        WorkspaceMembership.workspace_id == workspace_id,
                        WorkspaceMembership.status == "ACTIVE",
                        WorkspaceMembership.user_id.in_(ids),
                        Permission.code == permission_code,
                    )
                    .distinct()
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
