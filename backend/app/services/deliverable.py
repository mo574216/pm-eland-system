"""Deliverable preparation, readiness, submission, and withdrawal policy."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deliverable_workflow import (
    DELIVERABLE_STATES,
    DELIVERABLE_TRANSITIONS,
    DELIVERABLE_WORKFLOW_KEY,
    DELIVERABLE_WORKFLOW_NAME,
)
from app.core.exceptions import (
    FormValidationError,
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
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
from app.models.document import Document, DocumentVersion
from app.models.entity import EntityObject
from app.models.form import FormDefinition, FormInstance
from app.models.identity import AuditLog
from app.models.workflow import (
    WorkflowAssignment,
    WorkflowDefinition,
    WorkflowDefinitionVersion,
    WorkflowInstance,
    WorkflowStateDefinition,
    WorkflowTransitionDefinition,
    WorkflowTransitionEvent,
)
from app.repositories.deliverable import DeliverableRepository
from app.repositories.phase import PhaseRepository
from app.repositories.workflow import WorkflowRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.deliverable import (
    DeliverableAssigneeOption,
    DeliverableCreate,
    DeliverableReadiness,
    DeliverableResponse,
    DeliverableVersionCreate,
    DeliverableVersionResponse,
    PackageItemResponse,
    PackageResourceOption,
    ReviewActionResponse,
    ReviewCommentCreate,
    ReviewCommentResponse,
    ReviewOutcomeCreate,
    ReviewOutcomeResponse,
    SubmissionCreate,
    SubmissionResponse,
    SubmissionWithdrawalCreate,
)
from app.schemas.workflow import WorkflowTransitionRequest
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.phase import LockPolicyService
from app.services.workflow import WorkflowService


class DeliverableService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = DeliverableRepository(session)
        self.phase_repository = PhaseRepository(session)
        self.workspace_repository = WorkspaceRepository(session)
        self.workflow_repository = WorkflowRepository(session)
        self.workflow_service = WorkflowService(session, actor)
        self.lock_policy = LockPolicyService(session, actor)

    async def _ensure_workflow_profile(
        self, workspace_id: UUID
    ) -> tuple[WorkflowDefinitionVersion, WorkflowStateDefinition]:
        definition = await self.workflow_repository.definition_by_key(
            workspace_id, DELIVERABLE_WORKFLOW_KEY
        )
        version = (
            await self.workflow_repository.latest_published_version(definition.id)
            if definition is not None
            else None
        )
        if definition is not None and version is not None:
            initial = await self.workflow_repository.initial_state(version.id)
            if initial is None:
                raise ResourceConflictError
            return version, initial
        if definition is not None:
            raise ResourceConflictError
        definition = WorkflowDefinition(
            id=uuid4(),
            workspace_id=workspace_id,
            key=DELIVERABLE_WORKFLOW_KEY,
            name=DELIVERABLE_WORKFLOW_NAME,
            description="پروفایل پایه قابل نسخه‌بندی برای تحویل، بازبینی و ارسال رسمی",
            created_by=self.actor.user.id,
            version=1,
        )
        version = WorkflowDefinitionVersion(
            id=uuid4(),
            workspace_id=workspace_id,
            definition_id=definition.id,
            version_number=1,
            status="PUBLISHED",
            configuration={"system_profile": "DELIVERABLE_BASELINE"},
            created_by=self.actor.user.id,
            published_by=self.actor.user.id,
            published_at=datetime.now(UTC),
        )
        states = {
            key: WorkflowStateDefinition(
                id=uuid4(),
                workspace_id=workspace_id,
                definition_version_id=version.id,
                key=key,
                label=label,
                sequence_number=sequence,
                is_initial=is_initial,
                is_terminal=is_terminal,
                configuration={},
            )
            for key, label, sequence, is_initial, is_terminal in DELIVERABLE_STATES
        }
        transitions = [
            WorkflowTransitionDefinition(
                id=uuid4(),
                workspace_id=workspace_id,
                definition_version_id=version.id,
                key=key,
                label=label,
                from_state_id=states[from_key].id,
                to_state_id=states[to_key].id,
                required_permission=permission,
                authority_kind=authority,
                assignment_kind=assignment,
                reason_required=reason_required,
                policy=policy,
            )
            for (
                key,
                label,
                from_key,
                to_key,
                permission,
                authority,
                assignment,
                reason_required,
                policy,
            ) in DELIVERABLE_TRANSITIONS
        ]
        # These rows use composite workspace-scoped foreign keys. Persist each
        # dependency layer before handing its identifiers to the next layer; ORM
        # ordering cannot reliably infer this from the composite constraints.
        self.workflow_repository.add_all([definition])
        await self.workflow_repository.flush()
        self.workflow_repository.add_all([version])
        await self.workflow_repository.flush()
        self.workflow_repository.add_all(list(states.values()))
        await self.workflow_repository.flush()
        self.workflow_repository.add_all([*transitions])
        await self.workflow_repository.flush()
        return version, states["preparation"]

    async def _create_workflow_instance(
        self,
        deliverable: Deliverable,
        definition_version: WorkflowDefinitionVersion,
        initial: WorkflowStateDefinition,
        assignments: list[DeliverableAssignment],
    ) -> WorkflowInstance:
        instance = WorkflowInstance(
            id=uuid4(),
            workspace_id=deliverable.workspace_id,
            definition_version_id=definition_version.id,
            current_state_id=initial.id,
            target_kind="DELIVERABLE",
            target_id=deliverable.id,
            target_version=1,
            started_by=self.actor.user.id,
            version=1,
        )
        assignment_pairs = {(item.user_id, item.assignment_kind) for item in assignments}
        if deliverable.owner_id is not None:
            assignment_pairs.add((deliverable.owner_id, "CONTRIBUTOR"))
        workflow_assignments = [
            WorkflowAssignment(
                id=uuid4(),
                workspace_id=deliverable.workspace_id,
                instance_id=instance.id,
                user_id=user_id,
                assignment_kind=kind,
                assigned_by=self.actor.user.id,
            )
            for user_id, kind in assignment_pairs
        ]
        event = WorkflowTransitionEvent(
            id=uuid4(),
            workspace_id=deliverable.workspace_id,
            instance_id=instance.id,
            transition_id=None,
            definition_version_id=definition_version.id,
            previous_state_id=None,
            resulting_state_id=initial.id,
            action_key="START",
            authority_kind="CONFIGURATION",
            actor_id=self.actor.user.id,
            target_version=1,
            resulting_instance_version=1,
            reason=None,
            context={"profile": DELIVERABLE_WORKFLOW_KEY},
            idempotency_key=f"deliverable-start:{deliverable.id}",
        )
        # The assignment table has a composite FK to the instance. SQLAlchemy cannot
        # infer the required ordering from that composite constraint alone, so flush
        # the instance graph before adding its assignment/event children.
        self.workflow_repository.add_all([instance])
        await self.workflow_repository.flush()
        self.workflow_repository.add_all([*workflow_assignments, event])
        return instance

    async def _effective_permissions(self, workspace_id: UUID) -> frozenset[str]:
        if (
            await self.workspace_repository.accessible_workspace(workspace_id, self.actor.user.id)
            is None
        ):
            raise WorkspaceAccessDeniedError
        return self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )

    async def _require(self, workspace_id: UUID, permission: PermissionCode) -> None:
        if permission.value not in await self._effective_permissions(workspace_id):
            raise PermissionDeniedError

    def _audit(
        self,
        workspace_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str,
        after: dict[str, object],
        audit: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=audit.request_id,
            workspace_id=workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=None,
            after_state=after,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    async def _require_assignment(
        self, deliverable_id: UUID, allowed_kinds: set[str]
    ) -> tuple[DeliverableAssignment, ...]:
        assignments = await self.repository.assignments(deliverable_id)
        if not any(
            item.user_id == self.actor.user.id and item.assignment_kind in allowed_kinds
            for item in assignments
        ):
            raise PermissionDeniedError
        return assignments

    async def _resource_snapshot(
        self, workspace_id: UUID, kind: str, resource_id: UUID
    ) -> tuple[str, int | None]:
        if kind == "ENTITY":
            value = await self.session.scalar(
                select(EntityObject).where(
                    EntityObject.id == resource_id,
                    EntityObject.workspace_id == workspace_id,
                    EntityObject.deleted_at.is_(None),
                )
            )
            if value is not None:
                return value.name, value.version
        elif kind == "DOCUMENT_VERSION":
            document_row = (
                await self.session.execute(
                    select(DocumentVersion, Document.title)
                    .join(Document, Document.id == DocumentVersion.document_id)
                    .where(
                        DocumentVersion.id == resource_id,
                        Document.workspace_id == workspace_id,
                        Document.lifecycle_status != "DELETED",
                    )
                )
            ).one_or_none()
            if document_row is not None:
                version, title = document_row
                return f"{title} — نسخه {version.version_number}", version.version_number
        elif kind == "FORM_INSTANCE":
            form_row = (
                await self.session.execute(
                    select(FormInstance, FormDefinition.name)
                    .join(FormDefinition, FormDefinition.id == FormInstance.form_definition_id)
                    .where(
                        FormInstance.id == resource_id,
                        FormInstance.workspace_id == workspace_id,
                    )
                )
            ).one_or_none()
            if form_row is not None:
                instance, name = form_row
                return name, instance.version
        raise ResourceNotFoundError

    async def _version_response(self, value: DeliverableVersion) -> DeliverableVersionResponse:
        items = await self.repository.package_items(value.id)
        return DeliverableVersionResponse(
            id=value.id,
            version_number=value.version_number,
            summary=value.summary,
            created_by=value.created_by,
            created_at=value.created_at,
            items=[PackageItemResponse.model_validate(item) for item in items],
        )

    async def _submission_response(self, value: Submission) -> SubmissionResponse:
        recipients = await self.repository.recipients(value.id)
        withdrawal = await self.repository.latest_withdrawal(value.id)
        comments = await self.repository.review_comments(value.id)
        outcomes = await self.repository.review_outcomes(value.id)
        return SubmissionResponse(
            id=value.id,
            deliverable_version_id=value.deliverable_version_id,
            sequence_number=value.sequence_number,
            submission_kind=value.submission_kind,
            prior_submission_id=value.prior_submission_id,
            submitter_id=value.submitter_id,
            statement=value.statement,
            recipient_ids=[item.user_id for item in recipients],
            submitted_at=value.submitted_at,
            withdrawn_at=withdrawal.withdrawn_at if withdrawal else None,
            withdrawal_reason=withdrawal.reason if withdrawal else None,
            review_comments=[ReviewCommentResponse.model_validate(item) for item in comments],
            review_outcomes=[
                ReviewOutcomeResponse(
                    id=item.id,
                    submission_id=item.submission_id,
                    deliverable_version_id=item.deliverable_version_id,
                    outcome_kind=item.outcome_kind,
                    authority_kind=item.authority_kind,
                    actor_id=item.actor_id,
                    statement=item.statement,
                    conditions=item.conditions,
                    related_comment_ids=[UUID(value) for value in item.related_comment_ids],
                    created_at=item.created_at,
                )
                for item in outcomes
            ],
            available_review_actions=await self._review_actions(value, withdrawal is not None),
        )

    async def _review_actions(
        self, submission: Submission, withdrawn: bool
    ) -> list[ReviewActionResponse]:
        if withdrawn or not await self.repository.is_submission_recipient(
            submission.id, self.actor.user.id
        ):
            return []
        latest = await self.repository.latest_submission(submission.deliverable_id)
        if latest is None or latest.id != submission.id:
            return []
        instance = await self.workflow_repository.instance_for_target(
            submission.workspace_id, "DELIVERABLE", submission.deliverable_id
        )
        state = (
            await self.workflow_repository.state(instance.current_state_id)
            if instance is not None
            else None
        )
        if state is None or state.key != "submitted":
            return []
        permissions = await self._effective_permissions(submission.workspace_id)
        actions: list[ReviewActionResponse] = []
        definitions = (
            ("CLARIFICATION", "PROJECT_REVIEW", "ثبت درخواست شفاف‌سازی", False, "PROJECT_REVIEW"),
            ("REVISION_REQUEST", "PROJECT_REVIEW", "درخواست اصلاح پروژه", True, "PROJECT_REVIEW"),
            (
                "REJECTION_MAJOR_REVISION",
                "PROJECT_REVIEW",
                "رد و درخواست بازنگری اساسی",
                True,
                "PROJECT_REVIEW",
            ),
            ("RECOMMENDATION", "PROJECT_REVIEW", "توصیه مدیر پروژه", False, "PROJECT_RECOMMEND"),
            (
                "CONDITIONAL_RECOMMENDATION",
                "PROJECT_REVIEW",
                "توصیه مشروط مدیر پروژه",
                False,
                "PROJECT_RECOMMEND",
            ),
            (
                "CLARIFICATION",
                "TECHNICAL_REVIEW",
                "درخواست شفاف‌سازی فنی",
                False,
                "TECHNICAL_REVIEW",
            ),
            ("REVISION_REQUEST", "TECHNICAL_REVIEW", "درخواست اصلاح فنی", True, "TECHNICAL_REVIEW"),
            (
                "REJECTION_MAJOR_REVISION",
                "TECHNICAL_REVIEW",
                "رد فنی و بازنگری اساسی",
                True,
                "TECHNICAL_REVIEW",
            ),
            ("RECOMMENDATION", "TECHNICAL_REVIEW", "توصیه فنی", False, "TECHNICAL_REVIEW"),
            (
                "CONDITIONAL_RECOMMENDATION",
                "TECHNICAL_REVIEW",
                "توصیه فنی مشروط",
                False,
                "TECHNICAL_REVIEW",
            ),
            ("TECHNICAL_SIGN_OFF", "TECHNICAL_REVIEW", "تأیید فنی", False, "TECHNICAL_SIGN_OFF"),
        )
        for kind, authority, label, changes_workflow, permission in definitions:
            if permission in permissions:
                actions.append(
                    ReviewActionResponse(
                        outcome_kind=kind,
                        authority_kind=authority,
                        label=label,
                        changes_workflow=changes_workflow,
                    )
                )
        return actions

    @staticmethod
    def _readiness(
        value: Deliverable, items: tuple[DeliverablePackageItem, ...]
    ) -> DeliverableReadiness:
        required = [item for item in value.requirements if item.get("required", True)]
        completed_keys = {
            str(item.metadata_snapshot.get("requirement_key"))
            for item in items
            if item.metadata_snapshot.get("requirement_key")
        }
        missing = [
            str(item.get("label", item.get("key", "")))
            for item in required
            if item.get("key") not in completed_keys
        ]
        return DeliverableReadiness(
            ready=bool(items) and not missing,
            total_required=len(required),
            completed_required=len(required) - len(missing),
            missing=missing,
        )

    async def _response(self, value: Deliverable) -> DeliverableResponse:
        assignments = await self.repository.assignments(value.id)
        latest_version = await self.repository.latest_version(value.id)
        items = await self.repository.package_items(latest_version.id) if latest_version else ()
        latest_submission = await self.repository.latest_submission(value.id)
        workflow_instance = await self.workflow_repository.instance_for_target(
            value.workspace_id, "DELIVERABLE", value.id
        )
        return DeliverableResponse(
            id=value.id,
            workspace_id=value.workspace_id,
            phase_id=value.phase_id,
            key=value.key,
            name=value.name,
            description=value.description,
            owner_id=value.owner_id,
            internal_reviewer_id=value.internal_reviewer_id,
            contributor_ids=[
                item.user_id for item in assignments if item.assignment_kind == "CONTRIBUTOR"
            ],
            internal_due_at=value.internal_due_at,
            official_due_at=value.official_due_at,
            requirements=value.requirements,
            readiness=self._readiness(value, items),
            latest_version=await self._version_response(latest_version) if latest_version else None,
            latest_submission=(
                await self._submission_response(latest_submission) if latest_submission else None
            ),
            workflow=(
                await self.workflow_service.get_instance(workflow_instance.id)
                if workflow_instance is not None
                else None
            ),
            created_at=value.created_at,
            updated_at=value.updated_at,
            version=value.version,
        )

    async def create(
        self, phase_id: UUID, payload: DeliverableCreate, audit: AuditContext
    ) -> DeliverableResponse:
        async with self.session.begin():
            phase = await self.lock_policy.assert_phase_mutable(phase_id)
            await self._require(phase.workspace_id, PermissionCode.PHASE_MANAGE)
            participant_ids = {
                payload.owner_id,
                *payload.contributor_ids,
                *([payload.internal_reviewer_id] if payload.internal_reviewer_id else []),
            }
            if (
                await self.repository.active_member_ids(phase.workspace_id, participant_ids)
                != participant_ids
            ):
                raise ResourceNotFoundError
            contributor_ids = {payload.owner_id, *payload.contributor_ids}
            if (
                await self.repository.active_member_ids_with_permission(
                    phase.workspace_id, contributor_ids, PermissionCode.DELIVERABLE_CONTRIBUTE.value
                )
                != contributor_ids
            ):
                raise PermissionDeniedError
            if (
                await self.repository.active_member_ids_with_permission(
                    phase.workspace_id,
                    {payload.internal_reviewer_id},
                    PermissionCode.DELIVERABLE_INTERNAL_REVIEW.value,
                )
                != {payload.internal_reviewer_id}
            ):
                raise PermissionDeniedError
            value = Deliverable(
                id=uuid4(),
                workspace_id=phase.workspace_id,
                phase_id=phase.id,
                key=f"deliverable_{uuid4().hex}",
                name=payload.name,
                description=payload.description,
                owner_id=payload.owner_id,
                internal_reviewer_id=payload.internal_reviewer_id,
                internal_due_at=payload.internal_due_at,
                official_due_at=payload.official_due_at,
                requirements=[item.model_dump(mode="json") for item in payload.requirements],
                created_by=self.actor.user.id,
                version=1,
            )
            assignments = [
                DeliverableAssignment(
                    id=uuid4(),
                    workspace_id=phase.workspace_id,
                    deliverable_id=value.id,
                    user_id=payload.owner_id,
                    assignment_kind="OWNER",
                    assigned_by=self.actor.user.id,
                ),
                *[
                    DeliverableAssignment(
                        id=uuid4(),
                        workspace_id=phase.workspace_id,
                        deliverable_id=value.id,
                        user_id=user_id,
                        assignment_kind="CONTRIBUTOR",
                        assigned_by=self.actor.user.id,
                    )
                    for user_id in dict.fromkeys(payload.contributor_ids)
                ],
            ]
            if payload.internal_reviewer_id is not None:
                assignments.append(
                    DeliverableAssignment(
                        id=uuid4(),
                        workspace_id=phase.workspace_id,
                        deliverable_id=value.id,
                        user_id=payload.internal_reviewer_id,
                        assignment_kind="INTERNAL_REVIEWER",
                        assigned_by=self.actor.user.id,
                    )
                )
            workflow_version, initial_state = await self._ensure_workflow_profile(
                phase.workspace_id
            )
            self.repository.add_all([value, *assignments])
            workflow_instance = await self._create_workflow_instance(
                value, workflow_version, initial_state, assignments
            )
            self.repository.add_audit_log(
                self._audit(
                    phase.workspace_id,
                    "deliverable",
                    value.id,
                    "DELIVERABLE_CREATED",
                    {"phase_id": str(phase.id), "name": value.name},
                    audit,
                )
            )
            self.repository.add_audit_log(
                self._audit(
                    phase.workspace_id,
                    "workflow_instance",
                    workflow_instance.id,
                    "WORKFLOW_INSTANCE_STARTED",
                    {"state": initial_state.key, "target_kind": "DELIVERABLE"},
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return await self._response(value)

    async def assignment_options(
        self, phase_id: UUID, lane: str
    ) -> list[DeliverableAssigneeOption]:
        phase = await self.phase_repository.accessible_phase(phase_id, self.actor.user.id)
        if phase is None:
            raise ResourceNotFoundError
        await self._require(phase.workspace_id, PermissionCode.PHASE_MANAGE)
        permission = (
            PermissionCode.DELIVERABLE_INTERNAL_REVIEW
            if lane == "INTERNAL_REVIEWER"
            else PermissionCode.DELIVERABLE_CONTRIBUTE
        )
        rows = await self.repository.assignment_options(phase.workspace_id, permission.value)
        return [
            DeliverableAssigneeOption(
                user_id=row[0], username=row[1], display_name=row[2], role_code=row[3]
            )
            for row in rows
        ]

    async def list_for_phase(self, phase_id: UUID) -> list[DeliverableResponse]:
        phase = await self.phase_repository.accessible_phase(phase_id, self.actor.user.id)
        if phase is None:
            raise ResourceNotFoundError
        await self._require(phase.workspace_id, PermissionCode.WORKSPACE_READ)
        return [
            await self._response(value)
            for value in await self.repository.list_for_phase(
                phase_id, phase.workspace_id, self.actor.user.id
            )
        ]

    async def get(self, deliverable_id: UUID) -> DeliverableResponse:
        value = await self.repository.accessible(deliverable_id, self.actor.user.id)
        if value is None:
            raise ResourceNotFoundError
        await self._require(value.workspace_id, PermissionCode.WORKSPACE_READ)
        return await self._response(value)

    async def package_options(
        self,
        deliverable_id: UUID,
        kind: Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"],
        search: str,
        limit: int,
    ) -> list[PackageResourceOption]:
        value = await self.repository.accessible(deliverable_id, self.actor.user.id)
        if value is None:
            raise ResourceNotFoundError
        await self._require(value.workspace_id, PermissionCode.DELIVERABLE_CONTRIBUTE)
        await self._require_assignment(value.id, {"OWNER", "CONTRIBUTOR"})
        pattern = f"%{search.strip()}%"
        if kind == "ENTITY":
            rows = (
                await self.session.execute(
                    select(EntityObject.id, EntityObject.name, EntityObject.version)
                    .where(
                        EntityObject.workspace_id == value.workspace_id,
                        EntityObject.deleted_at.is_(None),
                        EntityObject.name.ilike(pattern),
                    )
                    .order_by(EntityObject.name, EntityObject.id)
                    .limit(limit)
                )
            ).all()
        elif kind == "DOCUMENT_VERSION":
            rows = (
                await self.session.execute(
                    select(DocumentVersion.id, Document.title, DocumentVersion.version_number)
                    .join(Document, Document.current_version_id == DocumentVersion.id)
                    .where(
                        Document.workspace_id == value.workspace_id,
                        Document.lifecycle_status == "ACTIVE",
                        Document.title.ilike(pattern),
                    )
                    .order_by(Document.title, Document.id)
                    .limit(limit)
                )
            ).all()
        elif kind == "FORM_INSTANCE":
            rows = (
                await self.session.execute(
                    select(FormInstance.id, FormDefinition.name, FormInstance.version)
                    .join(FormDefinition, FormDefinition.id == FormInstance.form_definition_id)
                    .where(
                        FormInstance.workspace_id == value.workspace_id,
                        FormDefinition.name.ilike(pattern),
                    )
                    .order_by(FormDefinition.name, FormInstance.id)
                    .limit(limit)
                )
            ).all()
        else:
            raise ResourceNotFoundError
        return [
            PackageResourceOption(
                id=row[0], resource_kind=kind, label=row[1], resource_version=row[2]
            )
            for row in rows
        ]

    async def create_version(
        self, deliverable_id: UUID, payload: DeliverableVersionCreate, audit: AuditContext
    ) -> DeliverableResponse:
        async with self.session.begin():
            value = await self.repository.accessible(deliverable_id, self.actor.user.id, lock=True)
            if value is None:
                raise ResourceNotFoundError
            await self._require(value.workspace_id, PermissionCode.DELIVERABLE_CONTRIBUTE)
            await self._require_assignment(value.id, {"OWNER", "CONTRIBUTOR"})
            await self.lock_policy.assert_phase_mutable(value.phase_id)
            workflow_instance = await self.workflow_repository.instance_for_target(
                value.workspace_id, "DELIVERABLE", value.id
            )
            if workflow_instance is None:
                raise ResourceConflictError
            workflow_state = await self.workflow_repository.state(
                workflow_instance.current_state_id
            )
            if workflow_state is None or workflow_state.key != "preparation":
                raise ResourceConflictError
            requirement_by_key = {str(item["key"]): item for item in value.requirements}
            records: list[DeliverablePackageItem] = []
            version = DeliverableVersion(
                id=uuid4(),
                workspace_id=value.workspace_id,
                deliverable_id=value.id,
                version_number=await self.repository.next_version_number(value.id),
                summary=payload.summary,
                context_snapshot={"phase_id": str(value.phase_id), "deliverable_name": value.name},
                created_by=self.actor.user.id,
            )
            seen: set[tuple[str, UUID]] = set()
            for item in payload.items:
                if (item.resource_kind, item.resource_id) in seen:
                    raise FormValidationError({"reason": "duplicate_package_item"})
                seen.add((item.resource_kind, item.resource_id))
                requirement = requirement_by_key.get(item.requirement_key or "")
                if item.requirement_key and (
                    requirement is None or requirement.get("resource_kind") != item.resource_kind
                ):
                    raise FormValidationError({"reason": "incompatible_requirement"})
                label, resource_version = await self._resource_snapshot(
                    value.workspace_id, item.resource_kind, item.resource_id
                )
                records.append(
                    DeliverablePackageItem(
                        id=uuid4(),
                        workspace_id=value.workspace_id,
                        deliverable_version_id=version.id,
                        resource_kind=item.resource_kind,
                        resource_id=item.resource_id,
                        resource_version=resource_version,
                        label_snapshot=label,
                        is_required=bool(requirement and requirement.get("required", True)),
                        metadata_snapshot={"requirement_key": item.requirement_key}
                        if item.requirement_key
                        else {},
                    )
                )
            # Package items reference the immutable version through a composite
            # workspace-scoped FK, so persist the version before its item records.
            self.repository.add_all([version])
            await self.repository.flush()
            self.repository.add_all([*records])
            self.repository.add_audit_log(
                self._audit(
                    value.workspace_id,
                    "deliverable_version",
                    version.id,
                    "DELIVERABLE_VERSION_CREATED",
                    {"deliverable_id": str(value.id), "version_number": version.version_number},
                    audit,
                )
            )
            await self.repository.flush()
        return await self._response(value)

    async def transition_review(
        self,
        deliverable_id: UUID,
        action_key: str,
        payload: WorkflowTransitionRequest,
        audit: AuditContext,
    ) -> DeliverableResponse:
        if action_key not in {"request_internal_review", "request_correction", "mark_ready"}:
            raise ResourceNotFoundError
        async with self.session.begin():
            value = await self.repository.accessible(deliverable_id, self.actor.user.id, lock=True)
            if value is None:
                raise ResourceNotFoundError
            await self.lock_policy.assert_phase_mutable(value.phase_id)
            workflow_instance = await self.workflow_repository.instance_for_target(
                value.workspace_id, "DELIVERABLE", value.id
            )
            if workflow_instance is None:
                raise ResourceConflictError
            await self.workflow_service.transition_instance(
                workflow_instance.id, action_key, payload, audit
            )
        return await self._response(value)

    async def submit(
        self, deliverable_id: UUID, payload: SubmissionCreate, audit: AuditContext
    ) -> DeliverableResponse:
        async with self.session.begin():
            value = await self.repository.accessible(deliverable_id, self.actor.user.id, lock=True)
            if value is None:
                raise ResourceNotFoundError
            await self._require(value.workspace_id, PermissionCode.SUBMISSION_CREATE)
            await self._require_assignment(value.id, {"OWNER"})
            await self.lock_policy.assert_phase_mutable(value.phase_id)
            replay = await self.repository.submission_by_idempotency(
                value.id, payload.idempotency_key
            )
            if replay is not None:
                return await self._response(value)
            version = await self.repository.version(value.id, payload.deliverable_version_id)
            if version is None:
                raise ResourceNotFoundError
            items = await self.repository.package_items(version.id)
            readiness = self._readiness(value, items)
            if not readiness.ready:
                raise FormValidationError(
                    {"reason": "deliverable_not_ready", "missing": readiness.missing}
                )
            recipient_ids = set(payload.recipient_ids)
            if (
                await self.repository.active_member_ids(value.workspace_id, recipient_ids)
                != recipient_ids
            ):
                raise ResourceNotFoundError
            latest = await self.repository.latest_submission(value.id)
            if payload.prior_submission_id != (latest.id if latest else None):
                raise ResourceConflictError
            sequence = latest.sequence_number + 1 if latest else 1
            submission = Submission(
                id=uuid4(),
                workspace_id=value.workspace_id,
                deliverable_id=value.id,
                deliverable_version_id=version.id,
                sequence_number=sequence,
                submission_kind="RESUBMISSION" if latest else "SUBMISSION",
                prior_submission_id=latest.id if latest else None,
                submitter_id=self.actor.user.id,
                statement=payload.statement,
                related_comment_ids=[str(item) for item in payload.related_comment_ids],
                context_snapshot=version.context_snapshot,
                idempotency_key=payload.idempotency_key,
            )
            recipients = [
                SubmissionRecipient(
                    id=uuid4(),
                    workspace_id=value.workspace_id,
                    submission_id=submission.id,
                    user_id=user_id,
                )
                for user_id in recipient_ids
            ]
            self.repository.add_all([submission, *recipients])
            await self.repository.flush()
            workflow_instance = await self.workflow_repository.instance_for_target(
                value.workspace_id, "DELIVERABLE", value.id
            )
            if workflow_instance is None:
                raise ResourceConflictError
            for recipient_id in recipient_ids:
                if not await self.workflow_repository.has_assignment(
                    workflow_instance.id, recipient_id, "REVIEW_RECIPIENT"
                ):
                    self.workflow_repository.add(
                        WorkflowAssignment(
                            id=uuid4(),
                            workspace_id=value.workspace_id,
                            instance_id=workflow_instance.id,
                            user_id=recipient_id,
                            assignment_kind="REVIEW_RECIPIENT",
                            assigned_by=self.actor.user.id,
                        )
                    )
            await self.workflow_service.transition_instance(
                workflow_instance.id,
                "formal_submit",
                WorkflowTransitionRequest(
                    expected_version=workflow_instance.version,
                    idempotency_key=f"{payload.idempotency_key}:workflow",
                    target_version=version.version_number,
                ),
                audit,
            )
            self.repository.add_audit_log(
                self._audit(
                    value.workspace_id,
                    "submission",
                    submission.id,
                    "FORMAL_SUBMISSION_CREATED",
                    {
                        "deliverable_id": str(value.id),
                        "version_id": str(version.id),
                        "sequence_number": sequence,
                    },
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return await self._response(value)

    async def withdraw(
        self, submission_id: UUID, payload: SubmissionWithdrawalCreate, audit: AuditContext
    ) -> SubmissionResponse:
        async with self.session.begin():
            submission = await self.repository.submission(submission_id, self.actor.user.id)
            if submission is None:
                raise ResourceNotFoundError
            await self._require(submission.workspace_id, PermissionCode.SUBMISSION_CREATE)
            deliverable = await self.repository.accessible(
                submission.deliverable_id, self.actor.user.id, lock=True
            )
            if deliverable is None:
                raise ResourceNotFoundError
            await self._require_assignment(deliverable.id, {"OWNER"})
            await self.lock_policy.assert_phase_mutable(deliverable.phase_id)
            replay = await self.repository.withdrawal_by_idempotency(
                submission.id, payload.idempotency_key
            )
            if replay is not None:
                return await self._submission_response(submission)
            if await self.repository.latest_withdrawal(submission.id) is not None:
                raise ResourceConflictError
            latest = await self.repository.latest_submission(deliverable.id)
            if latest is None or latest.id != submission.id:
                raise ResourceConflictError
            withdrawal = SubmissionWithdrawal(
                id=uuid4(),
                workspace_id=submission.workspace_id,
                submission_id=submission.id,
                withdrawn_by=self.actor.user.id,
                reason=payload.reason,
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([withdrawal])
            await self.repository.flush()
            workflow_instance = await self.workflow_repository.instance_for_target(
                submission.workspace_id, "DELIVERABLE", deliverable.id
            )
            if workflow_instance is None:
                raise ResourceConflictError
            await self.workflow_service.transition_instance(
                workflow_instance.id,
                "withdraw_submission",
                WorkflowTransitionRequest(
                    expected_version=workflow_instance.version,
                    idempotency_key=f"{payload.idempotency_key}:workflow",
                    reason=payload.reason,
                    target_version=workflow_instance.target_version,
                ),
                audit,
            )
            self.repository.add_audit_log(
                self._audit(
                    submission.workspace_id,
                    "submission",
                    submission.id,
                    "FORMAL_SUBMISSION_WITHDRAWN",
                    {"reason": payload.reason},
                    audit,
                )
            )
            await self.repository.flush()
        return await self._submission_response(submission)

    async def add_review_comment(
        self, submission_id: UUID, payload: ReviewCommentCreate, audit: AuditContext
    ) -> SubmissionResponse:
        async with self.session.begin():
            submission = await self.repository.submission(submission_id, self.actor.user.id)
            if submission is None:
                raise ResourceNotFoundError
            permissions = await self._effective_permissions(submission.workspace_id)
            if not (
                {PermissionCode.PROJECT_REVIEW.value, PermissionCode.TECHNICAL_REVIEW.value}
                & permissions
            ):
                raise PermissionDeniedError
            if not await self.repository.is_submission_recipient(submission.id, self.actor.user.id):
                raise PermissionDeniedError
            replay = await self.repository.review_comment_by_idempotency(
                submission.id, payload.idempotency_key
            )
            if replay is not None:
                return await self._submission_response(submission)
            deliverable = await self.repository.accessible(
                submission.deliverable_id, self.actor.user.id
            )
            if deliverable is None:
                raise ResourceNotFoundError
            await self.lock_policy.assert_phase_mutable(deliverable.phase_id)
            latest = await self.repository.latest_submission(deliverable.id)
            if (
                latest is None
                or latest.id != submission.id
                or await self.repository.latest_withdrawal(submission.id)
            ):
                raise ResourceConflictError
            workflow_instance = await self.workflow_repository.instance_for_target(
                submission.workspace_id, "DELIVERABLE", deliverable.id
            )
            workflow_state = (
                await self.workflow_repository.state(workflow_instance.current_state_id)
                if workflow_instance is not None
                else None
            )
            if workflow_state is None or workflow_state.key != "submitted":
                raise ResourceConflictError
            comment = ReviewComment(
                id=uuid4(),
                workspace_id=submission.workspace_id,
                submission_id=submission.id,
                deliverable_version_id=submission.deliverable_version_id,
                author_id=self.actor.user.id,
                text=payload.text,
                status="OPEN",
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([comment])
            self.repository.add_audit_log(
                self._audit(
                    submission.workspace_id,
                    "review_comment",
                    comment.id,
                    "REVIEW_COMMENT_CREATED",
                    {
                        "submission_id": str(submission.id),
                        "version_id": str(submission.deliverable_version_id),
                    },
                    audit,
                )
            )
            await self.repository.flush()
        return await self._submission_response(submission)

    async def record_review_outcome(
        self, submission_id: UUID, payload: ReviewOutcomeCreate, audit: AuditContext
    ) -> SubmissionResponse:
        async with self.session.begin():
            submission = await self.repository.submission(submission_id, self.actor.user.id)
            if submission is None:
                raise ResourceNotFoundError
            if not await self.repository.is_submission_recipient(submission.id, self.actor.user.id):
                raise PermissionDeniedError
            permission = self._review_outcome_permission(payload)
            await self._require(submission.workspace_id, permission)
            replay = await self.repository.review_outcome_by_idempotency(
                submission.id, payload.idempotency_key
            )
            if replay is not None:
                return await self._submission_response(submission)
            deliverable = await self.repository.accessible(
                submission.deliverable_id, self.actor.user.id, lock=True
            )
            if deliverable is None:
                raise ResourceNotFoundError
            await self.lock_policy.assert_phase_mutable(deliverable.phase_id)
            latest = await self.repository.latest_submission(deliverable.id)
            if (
                latest is None
                or latest.id != submission.id
                or await self.repository.latest_withdrawal(submission.id)
            ):
                raise ResourceConflictError
            workflow_instance = await self.workflow_repository.instance_for_target(
                submission.workspace_id, "DELIVERABLE", deliverable.id
            )
            workflow_state = (
                await self.workflow_repository.state(workflow_instance.current_state_id)
                if workflow_instance is not None
                else None
            )
            if workflow_state is None or workflow_state.key != "submitted":
                raise ResourceConflictError
            comment_ids = set(payload.related_comment_ids)
            if (
                await self.repository.review_comments_by_ids(submission.id, comment_ids)
                != comment_ids
            ):
                raise ResourceNotFoundError
            outcome = ReviewOutcome(
                id=uuid4(),
                workspace_id=submission.workspace_id,
                submission_id=submission.id,
                deliverable_version_id=submission.deliverable_version_id,
                outcome_kind=payload.outcome_kind,
                authority_kind=payload.authority_kind,
                actor_id=self.actor.user.id,
                statement=payload.statement,
                conditions=payload.conditions,
                related_comment_ids=[str(value) for value in payload.related_comment_ids],
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([outcome])
            await self.repository.flush()
            changes_workflow = payload.outcome_kind in {
                "REVISION_REQUEST",
                "REJECTION_MAJOR_REVISION",
            }
            if changes_workflow:
                if workflow_instance is None:
                    raise ResourceConflictError
                action_key = (
                    "project_request_revision"
                    if payload.authority_kind == "PROJECT_REVIEW"
                    else "technical_request_revision"
                )
                version = await self.repository.version(
                    deliverable.id, submission.deliverable_version_id
                )
                if version is None:
                    raise ResourceNotFoundError
                await self.workflow_service.transition_instance(
                    workflow_instance.id,
                    action_key,
                    WorkflowTransitionRequest(
                        expected_version=payload.expected_workflow_version or 0,
                        idempotency_key=f"{payload.idempotency_key}:workflow",
                        reason=payload.statement,
                        target_version=version.version_number,
                    ),
                    audit,
                )
            self.repository.add_audit_log(
                self._audit(
                    submission.workspace_id,
                    "review_outcome",
                    outcome.id,
                    "REVIEW_OUTCOME_RECORDED",
                    {
                        "submission_id": str(submission.id),
                        "version_id": str(submission.deliverable_version_id),
                        "outcome_kind": payload.outcome_kind,
                        "authority_kind": payload.authority_kind,
                    },
                    audit,
                )
            )
            await self.repository.flush()
        return await self._submission_response(submission)

    @staticmethod
    def _review_outcome_permission(payload: ReviewOutcomeCreate) -> PermissionCode:
        if payload.authority_kind == "TECHNICAL_REVIEW":
            if payload.outcome_kind == "TECHNICAL_SIGN_OFF":
                return PermissionCode.TECHNICAL_SIGN_OFF
            return PermissionCode.TECHNICAL_REVIEW
        if payload.outcome_kind in {"RECOMMENDATION", "CONDITIONAL_RECOMMENDATION"}:
            return PermissionCode.PROJECT_RECOMMEND
        if payload.outcome_kind == "TECHNICAL_SIGN_OFF":
            raise PermissionDeniedError
        return PermissionCode.PROJECT_REVIEW
