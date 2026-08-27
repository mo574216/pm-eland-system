"""Workspace-isolated persistence for contractual acceptance evidence."""

from typing import cast
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acceptance import (
    AcceptanceClosure,
    AcceptanceCondition,
    AcceptanceConditionEvent,
    AcceptanceDecision,
    AcceptancePackage,
    AcceptancePackageItem,
)
from app.models.deliverable import (
    Deliverable,
    ReviewOutcome,
    Submission,
    SubmissionWithdrawal,
)
from app.models.identity import AuditLog, Permission, Role, User, role_permissions
from app.models.workspace import WorkspaceMembership


class AcceptanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_all(self, values: list[object]) -> None:
        self.session.add_all(values)

    def add_audit_log(self, value: AuditLog) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def package_by_idempotency(self, phase_id: UUID, key: str) -> AcceptancePackage | None:
        return cast(
            AcceptancePackage | None,
            await self.session.scalar(
                select(AcceptancePackage).where(
                    AcceptancePackage.phase_id == phase_id,
                    AcceptancePackage.idempotency_key == key,
                )
            ),
        )

    async def next_package_sequence(self, phase_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(AcceptancePackage.sequence_number)).where(
                AcceptancePackage.phase_id == phase_id
            )
        )
        return int(current or 0) + 1

    async def phase_deliverables(self, phase_id: UUID) -> tuple[Deliverable, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(Deliverable)
                    .where(Deliverable.phase_id == phase_id)
                    .order_by(Deliverable.created_at, Deliverable.id)
                )
            ).all()
        )

    async def active_member_ids(self, workspace_id: UUID, user_ids: set[UUID]) -> set[UUID]:
        if not user_ids:
            return set()
        return set(
            (
                await self.session.scalars(
                    select(WorkspaceMembership.user_id).where(
                        WorkspaceMembership.workspace_id == workspace_id,
                        WorkspaceMembership.user_id.in_(user_ids),
                        WorkspaceMembership.status == "ACTIVE",
                    )
                )
            ).all()
        )

    async def member_ids_with_permission(
        self, workspace_id: UUID, user_ids: set[UUID], permission_code: str
    ) -> set[UUID]:
        if not user_ids:
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
                        WorkspaceMembership.user_id.in_(user_ids),
                        WorkspaceMembership.status == "ACTIVE",
                        Permission.code == permission_code,
                    )
                    .distinct()
                )
            ).all()
        )

    async def acceptance_recipient_options(
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

    async def latest_active_submission(self, deliverable_id: UUID) -> Submission | None:
        return cast(
            Submission | None,
            await self.session.scalar(
                select(Submission)
                .where(
                    Submission.deliverable_id == deliverable_id,
                    ~select(SubmissionWithdrawal.id)
                    .where(SubmissionWithdrawal.submission_id == Submission.id)
                    .exists(),
                )
                .order_by(Submission.sequence_number.desc())
                .limit(1)
            ),
        )

    async def latest_active_submission_by_id(self, submission_id: UUID) -> Submission | None:
        return cast(
            Submission | None,
            await self.session.scalar(
                select(Submission).where(
                    Submission.id == submission_id,
                    ~select(SubmissionWithdrawal.id)
                    .where(SubmissionWithdrawal.submission_id == Submission.id)
                    .exists(),
                )
            ),
        )

    async def recommendation_outcomes(self, submission_id: UUID) -> tuple[ReviewOutcome, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(ReviewOutcome).where(
                        ReviewOutcome.submission_id == submission_id,
                        ReviewOutcome.authority_kind == "PROJECT_REVIEW",
                        ReviewOutcome.outcome_kind.in_(
                            ("RECOMMENDATION", "CONDITIONAL_RECOMMENDATION")
                        ),
                    )
                )
            ).all()
        )

    async def packages_for_phase(
        self, phase_id: UUID, user_id: UUID
    ) -> tuple[AcceptancePackage, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(AcceptancePackage)
                    .join(
                        WorkspaceMembership,
                        WorkspaceMembership.workspace_id == AcceptancePackage.workspace_id,
                    )
                    .where(
                        AcceptancePackage.phase_id == phase_id,
                        WorkspaceMembership.user_id == user_id,
                        WorkspaceMembership.status == "ACTIVE",
                    )
                    .order_by(AcceptancePackage.sequence_number.desc())
                )
            ).all()
        )

    async def accessible_package(
        self, package_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> AcceptancePackage | None:
        statement = (
            select(AcceptancePackage)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == AcceptancePackage.workspace_id,
            )
            .where(
                AcceptancePackage.id == package_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update()
        return cast(AcceptancePackage | None, await self.session.scalar(statement))

    async def package_items(self, package_id: UUID) -> tuple[AcceptancePackageItem, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(AcceptancePackageItem)
                    .where(AcceptancePackageItem.acceptance_package_id == package_id)
                    .order_by(AcceptancePackageItem.label_snapshot, AcceptancePackageItem.id)
                )
            ).all()
        )

    async def decision(self, package_id: UUID) -> AcceptanceDecision | None:
        return cast(
            AcceptanceDecision | None,
            await self.session.scalar(
                select(AcceptanceDecision).where(
                    AcceptanceDecision.acceptance_package_id == package_id
                )
            ),
        )

    async def conditions(self, decision_id: UUID) -> tuple[AcceptanceCondition, ...]:
        return tuple(
            (
                await self.session.scalars(
                    select(AcceptanceCondition)
                    .where(AcceptanceCondition.decision_id == decision_id)
                    .order_by(AcceptanceCondition.due_at, AcceptanceCondition.id)
                )
            ).all()
        )

    async def closure(self, decision_id: UUID) -> AcceptanceClosure | None:
        return cast(
            AcceptanceClosure | None,
            await self.session.scalar(
                select(AcceptanceClosure).where(AcceptanceClosure.decision_id == decision_id)
            ),
        )

    async def accessible_condition(
        self, condition_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> AcceptanceCondition | None:
        statement = (
            select(AcceptanceCondition)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == AcceptanceCondition.workspace_id,
            )
            .where(
                AcceptanceCondition.id == condition_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update()
        return cast(AcceptanceCondition | None, await self.session.scalar(statement))

    async def condition_event_by_idempotency(
        self, condition_id: UUID, key: str
    ) -> AcceptanceConditionEvent | None:
        return cast(
            AcceptanceConditionEvent | None,
            await self.session.scalar(
                select(AcceptanceConditionEvent).where(
                    AcceptanceConditionEvent.condition_id == condition_id,
                    AcceptanceConditionEvent.idempotency_key == key,
                )
            ),
        )

    async def update_condition(
        self, condition_id: UUID, expected_version: int, status: str
    ) -> AcceptanceCondition | None:
        return cast(
            AcceptanceCondition | None,
            await self.session.scalar(
                update(AcceptanceCondition)
                .where(
                    AcceptanceCondition.id == condition_id,
                    AcceptanceCondition.version == expected_version,
                )
                .values(
                    status=status,
                    version=AcceptanceCondition.version + 1,
                    updated_at=func.now(),
                )
                .returning(AcceptanceCondition)
            ),
        )
