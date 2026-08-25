"""Persistence operations for generic governed workflows."""

from typing import cast
from uuid import UUID

from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deliverable import (
    Deliverable,
    DeliverablePackageItem,
    DeliverableVersion,
    Submission,
    SubmissionWithdrawal,
)
from app.models.document import Document
from app.models.entity import EntityObject
from app.models.form import FormInstance
from app.models.identity import AuditLog
from app.models.phase import Phase
from app.models.workflow import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowDefinitionVersion,
    WorkflowInstance,
    WorkflowStateDefinition,
    WorkflowTransitionDefinition,
    WorkflowTransitionEvent,
)
from app.models.workspace import WorkspaceMembership


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, value: object) -> None:
        self.session.add(value)

    def add_all(self, values: list[object]) -> None:
        self.session.add_all(values)

    def add_audit_log(self, value: AuditLog) -> None:
        self.session.add(value)

    async def flush(self) -> None:
        await self.session.flush()

    async def definition_by_key(self, workspace_id: UUID, key: str) -> WorkflowDefinition | None:
        return cast(
            WorkflowDefinition | None,
            await self.session.scalar(
                select(WorkflowDefinition).where(
                    WorkflowDefinition.workspace_id == workspace_id,
                    WorkflowDefinition.key == key,
                )
            ),
        )

    async def latest_published_version(
        self, definition_id: UUID
    ) -> WorkflowDefinitionVersion | None:
        return cast(
            WorkflowDefinitionVersion | None,
            await self.session.scalar(
                select(WorkflowDefinitionVersion)
                .where(
                    WorkflowDefinitionVersion.definition_id == definition_id,
                    WorkflowDefinitionVersion.status == "PUBLISHED",
                )
                .order_by(WorkflowDefinitionVersion.version_number.desc())
                .limit(1)
            ),
        )

    async def instance_for_target(
        self, workspace_id: UUID, target_kind: str, target_id: UUID
    ) -> WorkflowInstance | None:
        return cast(
            WorkflowInstance | None,
            await self.session.scalar(
                select(WorkflowInstance).where(
                    WorkflowInstance.workspace_id == workspace_id,
                    WorkflowInstance.target_kind == target_kind,
                    WorkflowInstance.target_id == target_id,
                )
            ),
        )

    async def accessible_definition(
        self, definition_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> WorkflowDefinition | None:
        statement = (
            select(WorkflowDefinition)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == WorkflowDefinition.workspace_id,
            )
            .where(
                WorkflowDefinition.id == definition_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update()
        return cast(WorkflowDefinition | None, await self.session.scalar(statement))

    async def version(self, version_id: UUID) -> WorkflowDefinitionVersion | None:
        return cast(
            WorkflowDefinitionVersion | None,
            await self.session.get(WorkflowDefinitionVersion, version_id),
        )

    async def initial_state(self, version_id: UUID) -> WorkflowStateDefinition | None:
        return cast(
            WorkflowStateDefinition | None,
            await self.session.scalar(
                select(WorkflowStateDefinition).where(
                    WorkflowStateDefinition.definition_version_id == version_id,
                    WorkflowStateDefinition.is_initial.is_(True),
                )
            ),
        )

    async def state(self, state_id: UUID) -> WorkflowStateDefinition | None:
        return cast(
            WorkflowStateDefinition | None,
            await self.session.get(WorkflowStateDefinition, state_id),
        )

    async def states(self, state_ids: set[UUID]) -> dict[UUID, WorkflowStateDefinition]:
        if not state_ids:
            return {}
        values = (
            await self.session.scalars(
                select(WorkflowStateDefinition).where(WorkflowStateDefinition.id.in_(state_ids))
            )
        ).all()
        return {value.id: value for value in values}

    async def publish_version(
        self, version_id: UUID, *, actor_id: UUID
    ) -> WorkflowDefinitionVersion | None:
        return cast(
            WorkflowDefinitionVersion | None,
            await self.session.scalar(
                update(WorkflowDefinitionVersion)
                .where(
                    WorkflowDefinitionVersion.id == version_id,
                    WorkflowDefinitionVersion.status == "DRAFT",
                )
                .values(status="PUBLISHED", published_by=actor_id, published_at=func.now())
                .returning(WorkflowDefinitionVersion)
            ),
        )

    async def next_version_number(self, definition_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(WorkflowDefinitionVersion.version_number)).where(
                WorkflowDefinitionVersion.definition_id == definition_id
            )
        )
        return int(current or 0) + 1

    async def bump_definition(
        self, definition_id: UUID, expected_version: int
    ) -> WorkflowDefinition | None:
        return cast(
            WorkflowDefinition | None,
            await self.session.scalar(
                update(WorkflowDefinition)
                .where(
                    WorkflowDefinition.id == definition_id,
                    WorkflowDefinition.version == expected_version,
                )
                .values(version=WorkflowDefinition.version + 1, updated_at=func.now())
                .returning(WorkflowDefinition)
            ),
        )

    async def accessible_instance(
        self, instance_id: UUID, user_id: UUID, *, lock: bool = False
    ) -> WorkflowInstance | None:
        statement = (
            select(WorkflowInstance)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == WorkflowInstance.workspace_id,
            )
            .where(
                WorkflowInstance.id == instance_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        if lock:
            statement = statement.with_for_update()
        return cast(WorkflowInstance | None, await self.session.scalar(statement))

    async def transition(
        self, version_id: UUID, state_id: UUID, key: str
    ) -> WorkflowTransitionDefinition | None:
        return cast(
            WorkflowTransitionDefinition | None,
            await self.session.scalar(
                select(WorkflowTransitionDefinition).where(
                    WorkflowTransitionDefinition.definition_version_id == version_id,
                    WorkflowTransitionDefinition.from_state_id == state_id,
                    WorkflowTransitionDefinition.key == key,
                )
            ),
        )

    async def transitions_from(
        self, version_id: UUID, state_id: UUID
    ) -> tuple[WorkflowTransitionDefinition, ...]:
        statement = (
            select(WorkflowTransitionDefinition)
            .where(
                WorkflowTransitionDefinition.definition_version_id == version_id,
                WorkflowTransitionDefinition.from_state_id == state_id,
            )
            .order_by(WorkflowTransitionDefinition.label, WorkflowTransitionDefinition.id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def has_assignment(self, instance_id: UUID, user_id: UUID, assignment_kind: str) -> bool:
        statement = select(WorkflowAssignment.id).where(
            WorkflowAssignment.instance_id == instance_id,
            WorkflowAssignment.user_id == user_id,
            WorkflowAssignment.assignment_kind == assignment_kind,
        )
        return await self.session.scalar(statement) is not None

    async def active_members(self, workspace_id: UUID, user_ids: set[UUID]) -> set[UUID]:
        if not user_ids:
            return set()
        statement = select(WorkspaceMembership.user_id).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id.in_(user_ids),
            WorkspaceMembership.status == "ACTIVE",
        )
        return set((await self.session.scalars(statement)).all())

    async def target_in_workspace(self, workspace_id: UUID, kind: str, target_id: UUID) -> bool:
        if kind == "ENTITY":
            statement = select(EntityObject.id).where(
                EntityObject.id == target_id, EntityObject.workspace_id == workspace_id
            )
        elif kind == "DOCUMENT":
            statement = select(Document.id).where(
                Document.id == target_id, Document.workspace_id == workspace_id
            )
        elif kind == "FORM_INSTANCE":
            statement = select(FormInstance.id).where(
                FormInstance.id == target_id, FormInstance.workspace_id == workspace_id
            )
        elif kind == "PHASE":
            statement = select(Phase.id).where(
                Phase.id == target_id, Phase.workspace_id == workspace_id
            )
        elif kind == "DELIVERABLE":
            statement = select(Deliverable.id).where(
                Deliverable.id == target_id, Deliverable.workspace_id == workspace_id
            )
        else:
            return False
        return await self.session.scalar(statement) is not None

    async def deliverable_package_is_ready(self, deliverable_id: UUID) -> bool:
        deliverable = await self.session.get(Deliverable, deliverable_id)
        if deliverable is None:
            return False
        version = await self.session.scalar(
            select(DeliverableVersion)
            .where(DeliverableVersion.deliverable_id == deliverable.id)
            .order_by(DeliverableVersion.version_number.desc())
            .limit(1)
        )
        if version is None:
            return False
        items = tuple(
            (
                await self.session.scalars(
                    select(DeliverablePackageItem).where(
                        DeliverablePackageItem.deliverable_version_id == version.id
                    )
                )
            ).all()
        )
        completed = {
            str(item.metadata_snapshot.get("requirement_key"))
            for item in items
            if item.metadata_snapshot.get("requirement_key")
        }
        required = {
            str(item.get("key")) for item in deliverable.requirements if item.get("required", True)
        }
        return bool(items) and required <= completed

    async def has_active_submission_version(
        self, deliverable_id: UUID, version_number: int | None
    ) -> bool:
        if version_number is None:
            return False
        statement = (
            select(Submission.id)
            .join(
                DeliverableVersion,
                DeliverableVersion.id == Submission.deliverable_version_id,
            )
            .where(
                Submission.deliverable_id == deliverable_id,
                DeliverableVersion.version_number == version_number,
                ~exists(
                    select(SubmissionWithdrawal.id).where(
                        SubmissionWithdrawal.submission_id == Submission.id
                    )
                ),
            )
        )
        return await self.session.scalar(statement) is not None

    async def latest_submission_is_withdrawn(self, deliverable_id: UUID) -> bool:
        latest_id = await self.session.scalar(
            select(Submission.id)
            .where(Submission.deliverable_id == deliverable_id)
            .order_by(Submission.sequence_number.desc())
            .limit(1)
        )
        if latest_id is None:
            return False
        return (
            await self.session.scalar(
                select(SubmissionWithdrawal.id).where(
                    SubmissionWithdrawal.submission_id == latest_id
                )
            )
            is not None
        )

    async def update_instance_state(
        self, instance_id: UUID, expected_version: int, state_id: UUID, target_version: int | None
    ) -> WorkflowInstance | None:
        values: dict[str, object] = {
            "current_state_id": state_id,
            "updated_at": func.now(),
            "version": WorkflowInstance.version + 1,
        }
        if target_version is not None:
            values["target_version"] = target_version
        return cast(
            WorkflowInstance | None,
            await self.session.scalar(
                update(WorkflowInstance)
                .where(
                    WorkflowInstance.id == instance_id,
                    WorkflowInstance.version == expected_version,
                )
                .values(**values)
                .returning(WorkflowInstance)
            ),
        )

    async def event_by_idempotency(
        self, instance_id: UUID, idempotency_key: str
    ) -> WorkflowTransitionEvent | None:
        return cast(
            WorkflowTransitionEvent | None,
            await self.session.scalar(
                select(WorkflowTransitionEvent).where(
                    WorkflowTransitionEvent.instance_id == instance_id,
                    WorkflowTransitionEvent.idempotency_key == idempotency_key,
                )
            ),
        )

    async def history(
        self, instance_id: UUID, *, page: int, page_size: int
    ) -> tuple[tuple[WorkflowTransitionEvent, ...], int]:
        filters = [WorkflowTransitionEvent.instance_id == instance_id]
        statement = (
            select(WorkflowTransitionEvent)
            .where(*filters)
            .order_by(WorkflowTransitionEvent.occurred_at.desc(), WorkflowTransitionEvent.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = tuple((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(select(func.count()).where(*filters))) or 0)
        return items, total
