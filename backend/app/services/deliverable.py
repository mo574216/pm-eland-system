"""Deliverable preparation, readiness, submission, and withdrawal policy."""

from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
    Submission,
    SubmissionRecipient,
    SubmissionWithdrawal,
)
from app.models.document import Document, DocumentVersion
from app.models.entity import EntityObject
from app.models.form import FormDefinition, FormInstance
from app.models.identity import AuditLog
from app.repositories.deliverable import DeliverableRepository
from app.repositories.phase import PhaseRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.deliverable import (
    DeliverableCreate,
    DeliverableReadiness,
    DeliverableResponse,
    DeliverableVersionCreate,
    DeliverableVersionResponse,
    PackageItemResponse,
    PackageResourceOption,
    SubmissionCreate,
    SubmissionResponse,
    SubmissionWithdrawalCreate,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService
from app.services.phase import LockPolicyService


class DeliverableService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = DeliverableRepository(session)
        self.phase_repository = PhaseRepository(session)
        self.workspace_repository = WorkspaceRepository(session)
        self.lock_policy = LockPolicyService(session, actor)

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
        )

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
            self.repository.add_all([value, *assignments])
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
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return await self._response(value)

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
            self.repository.add_all([version, *records])
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
