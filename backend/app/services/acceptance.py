"""Contractual phase acceptance policy with immutable evidence and authority separation."""

from datetime import UTC, datetime
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
    StaleVersionError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.acceptance import (
    AcceptanceClosure,
    AcceptanceCondition,
    AcceptanceConditionEvent,
    AcceptanceDecision,
    AcceptancePackage,
    AcceptancePackageItem,
)
from app.models.document import Document, DocumentVersion
from app.models.entity import EntityObject
from app.models.form import FormDefinition, FormInstance
from app.models.identity import AuditLog
from app.repositories.acceptance import AcceptanceRepository
from app.repositories.phase import PhaseRepository
from app.repositories.workflow import WorkflowRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.acceptance import (
    AcceptanceClosureCreate,
    AcceptanceConditionEvidenceCreate,
    AcceptanceConditionResponse,
    AcceptanceConditionVerificationCreate,
    AcceptanceDecisionCreate,
    AcceptanceDecisionResponse,
    AcceptancePackageCreate,
    AcceptancePackageItemResponse,
    AcceptancePackageResponse,
    AcceptanceWorkspaceResponse,
)
from app.schemas.deliverable import PackageResourceOption
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


class AcceptanceService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = AcceptanceRepository(session)
        self.phase_repository = PhaseRepository(session)
        self.workspace_repository = WorkspaceRepository(session)
        self.workflow_repository = WorkflowRepository(session)

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

    async def _condition_response(self, value: AcceptanceCondition) -> AcceptanceConditionResponse:
        permissions = await self._effective_permissions(value.workspace_id)
        actions: list[str] = []
        if value.responsible_id == self.actor.user.id and value.status in {
            "OPEN",
            "IN_PROGRESS",
            "REJECTED",
        }:
            actions.append("SUBMIT_EVIDENCE")
        if (
            value.verifier_id == self.actor.user.id
            and PermissionCode.CONDITION_VERIFY.value in permissions
            and value.status == "SUBMITTED_FOR_VERIFICATION"
        ):
            actions.extend(("VERIFY", "REJECT_EVIDENCE"))
        return AcceptanceConditionResponse(
            id=value.id,
            description=value.description,
            responsible_id=value.responsible_id,
            verifier_id=value.verifier_id,
            due_at=value.due_at,
            evidence_requirement=value.evidence_requirement,
            mandatory=value.mandatory,
            status=value.status,
            version=value.version,
            available_actions=actions,
        )

    async def _response(self, value: AcceptancePackage) -> AcceptancePackageResponse:
        items = await self.repository.package_items(value.id)
        decision = await self.repository.decision(value.id)
        decision_response = None
        if decision is not None:
            conditions = await self.repository.conditions(decision.id)
            closure = await self.repository.closure(decision.id)
            permissions = await self._effective_permissions(value.workspace_id)
            can_close = (
                decision.decision_kind == "CONDITIONAL_ACCEPT"
                and closure is None
                and value.employer_recipient_id == self.actor.user.id
                and PermissionCode.ACCEPTANCE_DECIDE.value in permissions
                and bool(conditions)
                and all(not item.mandatory or item.status == "SATISFIED" for item in conditions)
            )
            decision_response = AcceptanceDecisionResponse(
                id=decision.id,
                decision_kind=decision.decision_kind,
                actor_id=decision.actor_id,
                authority_kind=decision.authority_kind,
                statement=decision.statement,
                decided_at=decision.decided_at,
                conditions=[await self._condition_response(item) for item in conditions],
                closed_at=closure.closed_at if closure else None,
                closure_statement=closure.statement if closure else None,
                can_close=can_close,
            )
        permissions = await self._effective_permissions(value.workspace_id)
        available_decisions = (
            ["ACCEPT", "CONDITIONAL_ACCEPT", "REJECT"]
            if decision is None
            and value.employer_recipient_id == self.actor.user.id
            and PermissionCode.ACCEPTANCE_DECIDE.value in permissions
            else []
        )
        return AcceptancePackageResponse(
            id=value.id,
            workspace_id=value.workspace_id,
            phase_id=value.phase_id,
            sequence_number=value.sequence_number,
            statement=value.statement,
            employer_recipient_id=value.employer_recipient_id,
            requested_by=value.requested_by,
            created_at=value.created_at,
            items=[
                AcceptancePackageItemResponse(
                    id=item.id,
                    submission_id=item.submission_id,
                    deliverable_version_id=item.deliverable_version_id,
                    review_outcome_ids=[UUID(item_id) for item_id in item.review_outcome_ids],
                    label_snapshot=item.label_snapshot,
                )
                for item in items
            ],
            decision=decision_response,
            available_decisions=available_decisions,
        )

    async def list_for_phase(self, phase_id: UUID) -> list[AcceptancePackageResponse]:
        phase = await self.phase_repository.accessible_phase(phase_id, self.actor.user.id)
        if phase is None:
            raise ResourceNotFoundError
        await self._require(phase.workspace_id, PermissionCode.WORKSPACE_READ)
        return [
            await self._response(value)
            for value in await self.repository.packages_for_phase(phase.id, self.actor.user.id)
        ]

    async def workspace(self, phase_id: UUID) -> AcceptanceWorkspaceResponse:
        phase = await self.phase_repository.accessible_phase(phase_id, self.actor.user.id)
        if phase is None:
            raise ResourceNotFoundError
        permissions = await self._effective_permissions(phase.workspace_id)
        packages = [
            await self._response(value)
            for value in await self.repository.packages_for_phase(phase.id, self.actor.user.id)
        ]
        return AcceptanceWorkspaceResponse(
            can_prepare=(
                PermissionCode.PROJECT_RECOMMEND.value in permissions
                and not phase.is_locked
                and phase.status != "ARCHIVED"
            ),
            packages=packages,
        )

    async def create_package(
        self, phase_id: UUID, payload: AcceptancePackageCreate, audit: AuditContext
    ) -> AcceptancePackageResponse:
        async with self.session.begin():
            phase = await self.phase_repository.accessible_phase(
                phase_id, self.actor.user.id, lock=True
            )
            if phase is None:
                raise ResourceNotFoundError
            await self._require(phase.workspace_id, PermissionCode.PROJECT_RECOMMEND)
            if phase.is_locked or phase.status == "ARCHIVED":
                raise ResourceConflictError
            replay = await self.repository.package_by_idempotency(phase.id, payload.idempotency_key)
            if replay is not None:
                return await self._response(replay)
            if await self.repository.active_member_ids(
                phase.workspace_id, {payload.employer_recipient_id}
            ) != {payload.employer_recipient_id}:
                raise ResourceNotFoundError
            deliverables = await self.repository.phase_deliverables(phase.id)
            if not deliverables:
                raise FormValidationError({"reason": "acceptance_package_has_no_deliverables"})
            package = AcceptancePackage(
                id=uuid4(),
                workspace_id=phase.workspace_id,
                phase_id=phase.id,
                sequence_number=await self.repository.next_package_sequence(phase.id),
                statement=payload.statement,
                employer_recipient_id=payload.employer_recipient_id,
                requested_by=self.actor.user.id,
                evidence_snapshot={"phase_version": phase.version},
                idempotency_key=payload.idempotency_key,
            )
            items: list[AcceptancePackageItem] = []
            missing: list[str] = []
            for deliverable in deliverables:
                submission = await self.repository.latest_active_submission(deliverable.id)
                if submission is None:
                    missing.append(deliverable.name)
                    continue
                instance = await self.workflow_repository.instance_for_target(
                    phase.workspace_id, "DELIVERABLE", deliverable.id
                )
                state = (
                    await self.workflow_repository.state(instance.current_state_id)
                    if instance is not None
                    else None
                )
                recommendations = await self.repository.recommendation_outcomes(submission.id)
                if state is None or state.key != "submitted" or not recommendations:
                    missing.append(deliverable.name)
                    continue
                items.append(
                    AcceptancePackageItem(
                        id=uuid4(),
                        workspace_id=phase.workspace_id,
                        acceptance_package_id=package.id,
                        submission_id=submission.id,
                        deliverable_version_id=submission.deliverable_version_id,
                        review_outcome_ids=[str(item.id) for item in recommendations],
                        label_snapshot=deliverable.name,
                    )
                )
            if missing:
                raise FormValidationError(
                    {"reason": "acceptance_evidence_incomplete", "deliverables": missing}
                )
            self.repository.add_all([package, *items])
            self.repository.add_audit_log(
                self._audit(
                    phase.workspace_id,
                    "acceptance_package",
                    package.id,
                    "ACCEPTANCE_PACKAGE_CREATED",
                    {"phase_id": str(phase.id), "submission_count": len(items)},
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return await self._response(package)

    async def _assert_package_current(self, package: AcceptancePackage) -> None:
        for item in await self.repository.package_items(package.id):
            submission = await self.repository.latest_active_submission_by_id(item.submission_id)
            if (
                submission is None
                or submission.deliverable_version_id != item.deliverable_version_id
            ):
                raise ResourceConflictError
            latest = await self.repository.latest_active_submission(submission.deliverable_id)
            if latest is None or latest.id != submission.id:
                raise ResourceConflictError

    async def decide(
        self, package_id: UUID, payload: AcceptanceDecisionCreate, audit: AuditContext
    ) -> AcceptancePackageResponse:
        async with self.session.begin():
            package = await self.repository.accessible_package(
                package_id, self.actor.user.id, lock=True
            )
            if package is None:
                raise ResourceNotFoundError
            await self._require(package.workspace_id, PermissionCode.ACCEPTANCE_DECIDE)
            if package.employer_recipient_id != self.actor.user.id:
                raise PermissionDeniedError
            existing = await self.repository.decision(package.id)
            if existing is not None:
                if existing.idempotency_key == payload.idempotency_key:
                    return await self._response(package)
                raise ResourceConflictError
            await self._assert_package_current(package)
            member_ids = {
                member_id
                for condition in payload.conditions
                for member_id in (condition.responsible_id, condition.verifier_id)
            }
            if (
                await self.repository.active_member_ids(package.workspace_id, member_ids)
                != member_ids
            ):
                raise ResourceNotFoundError
            now = datetime.now(UTC)
            if any(condition.due_at <= now for condition in payload.conditions):
                raise FormValidationError({"reason": "condition_deadline_must_be_future"})
            decision = AcceptanceDecision(
                id=uuid4(),
                workspace_id=package.workspace_id,
                acceptance_package_id=package.id,
                decision_kind=payload.decision_kind,
                actor_id=self.actor.user.id,
                authority_kind="EMPLOYER_ACCEPTANCE",
                statement=payload.statement,
                idempotency_key=payload.idempotency_key,
            )
            conditions = [
                AcceptanceCondition(
                    id=uuid4(),
                    workspace_id=package.workspace_id,
                    decision_id=decision.id,
                    description=item.description,
                    responsible_id=item.responsible_id,
                    verifier_id=item.verifier_id,
                    due_at=item.due_at,
                    evidence_requirement=item.evidence_requirement,
                    mandatory=item.mandatory,
                    status="OPEN",
                    version=1,
                )
                for item in payload.conditions
            ]
            self.repository.add_all([decision, *conditions])
            if payload.decision_kind in {"ACCEPT", "CONDITIONAL_ACCEPT"}:
                await self.phase_repository.set_lock(
                    package.phase_id, locked=True, actor_id=self.actor.user.id
                )
            self.repository.add_audit_log(
                self._audit(
                    package.workspace_id,
                    "acceptance_decision",
                    decision.id,
                    "ACCEPTANCE_DECISION_RECORDED",
                    {
                        "package_id": str(package.id),
                        "decision_kind": payload.decision_kind,
                        "condition_count": len(conditions),
                    },
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return await self._response(package)

    async def _evidence_snapshot(
        self, workspace_id: UUID, kind: str, resource_id: UUID
    ) -> dict[str, object]:
        if kind == "ENTITY":
            value = await self.session.scalar(
                select(EntityObject).where(
                    EntityObject.id == resource_id,
                    EntityObject.workspace_id == workspace_id,
                    EntityObject.deleted_at.is_(None),
                )
            )
            if value is not None:
                return {
                    "resource_kind": kind,
                    "resource_id": str(value.id),
                    "version": value.version,
                }
        elif kind == "DOCUMENT_VERSION":
            value = await self.session.scalar(
                select(DocumentVersion)
                .join(Document, Document.id == DocumentVersion.document_id)
                .where(DocumentVersion.id == resource_id, Document.workspace_id == workspace_id)
            )
            if value is not None:
                return {
                    "resource_kind": kind,
                    "resource_id": str(value.id),
                    "version": value.version_number,
                }
        elif kind == "FORM_INSTANCE":
            value = await self.session.scalar(
                select(FormInstance).where(
                    FormInstance.id == resource_id,
                    FormInstance.workspace_id == workspace_id,
                )
            )
            if value is not None:
                return {
                    "resource_kind": kind,
                    "resource_id": str(value.id),
                    "version": value.version,
                }
        raise ResourceNotFoundError

    async def submit_condition_evidence(
        self,
        condition_id: UUID,
        payload: AcceptanceConditionEvidenceCreate,
        audit: AuditContext,
    ) -> AcceptanceConditionResponse:
        async with self.session.begin():
            condition = await self.repository.accessible_condition(
                condition_id, self.actor.user.id, lock=True
            )
            if condition is None:
                raise ResourceNotFoundError
            replay = await self.repository.condition_event_by_idempotency(
                condition.id, payload.idempotency_key
            )
            if replay is not None:
                return await self._condition_response(condition)
            if condition.responsible_id != self.actor.user.id or condition.status not in {
                "OPEN",
                "IN_PROGRESS",
                "REJECTED",
            }:
                raise PermissionDeniedError
            evidence = [
                await self._evidence_snapshot(
                    condition.workspace_id, item.resource_kind, item.resource_id
                )
                for item in payload.evidence
            ]
            previous = condition.status
            updated = await self.repository.update_condition(
                condition.id, payload.expected_version, "SUBMITTED_FOR_VERIFICATION"
            )
            if updated is None:
                raise StaleVersionError
            event = AcceptanceConditionEvent(
                id=uuid4(),
                workspace_id=condition.workspace_id,
                condition_id=condition.id,
                action_kind="SUBMIT_EVIDENCE",
                actor_id=self.actor.user.id,
                previous_status=previous,
                resulting_status=updated.status,
                statement=payload.statement,
                evidence=evidence,
                resulting_version=updated.version,
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([event])
            self.repository.add_audit_log(
                self._audit(
                    condition.workspace_id,
                    "acceptance_condition",
                    condition.id,
                    "CONDITION_EVIDENCE_SUBMITTED",
                    {"evidence_count": len(evidence), "version": updated.version},
                    audit,
                )
            )
            await self.repository.flush()
        return await self._condition_response(updated)

    async def evidence_options(
        self,
        condition_id: UUID,
        kind: Literal["ENTITY", "DOCUMENT_VERSION", "FORM_INSTANCE"],
        search: str,
        limit: int,
    ) -> list[PackageResourceOption]:
        condition = await self.repository.accessible_condition(condition_id, self.actor.user.id)
        if condition is None:
            raise ResourceNotFoundError
        if condition.responsible_id != self.actor.user.id:
            raise PermissionDeniedError
        pattern = f"%{search.strip()}%"
        if kind == "ENTITY":
            rows = (
                await self.session.execute(
                    select(EntityObject.id, EntityObject.name, EntityObject.version)
                    .where(
                        EntityObject.workspace_id == condition.workspace_id,
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
                        Document.workspace_id == condition.workspace_id,
                        Document.lifecycle_status == "ACTIVE",
                        Document.title.ilike(pattern),
                    )
                    .order_by(Document.title, Document.id)
                    .limit(limit)
                )
            ).all()
        else:
            rows = (
                await self.session.execute(
                    select(FormInstance.id, FormDefinition.name, FormInstance.version)
                    .join(FormDefinition, FormDefinition.id == FormInstance.form_definition_id)
                    .where(
                        FormInstance.workspace_id == condition.workspace_id,
                        FormDefinition.name.ilike(pattern),
                    )
                    .order_by(FormDefinition.name, FormInstance.id)
                    .limit(limit)
                )
            ).all()
        return [
            PackageResourceOption(
                id=row[0], resource_kind=kind, label=row[1], resource_version=row[2]
            )
            for row in rows
        ]

    async def verify_condition(
        self,
        condition_id: UUID,
        payload: AcceptanceConditionVerificationCreate,
        audit: AuditContext,
    ) -> AcceptanceConditionResponse:
        async with self.session.begin():
            condition = await self.repository.accessible_condition(
                condition_id, self.actor.user.id, lock=True
            )
            if condition is None:
                raise ResourceNotFoundError
            await self._require(condition.workspace_id, PermissionCode.CONDITION_VERIFY)
            if condition.verifier_id != self.actor.user.id:
                raise PermissionDeniedError
            replay = await self.repository.condition_event_by_idempotency(
                condition.id, payload.idempotency_key
            )
            if replay is not None:
                return await self._condition_response(condition)
            if condition.status != "SUBMITTED_FOR_VERIFICATION":
                raise ResourceConflictError
            resulting = "SATISFIED" if payload.decision == "VERIFY" else "REJECTED"
            previous = condition.status
            updated = await self.repository.update_condition(
                condition.id, payload.expected_version, resulting
            )
            if updated is None:
                raise StaleVersionError
            event = AcceptanceConditionEvent(
                id=uuid4(),
                workspace_id=condition.workspace_id,
                condition_id=condition.id,
                action_kind=payload.decision,
                actor_id=self.actor.user.id,
                previous_status=previous,
                resulting_status=updated.status,
                statement=payload.statement,
                evidence=[],
                resulting_version=updated.version,
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([event])
            self.repository.add_audit_log(
                self._audit(
                    condition.workspace_id,
                    "acceptance_condition",
                    condition.id,
                    "CONDITION_VERIFICATION_RECORDED",
                    {"decision": payload.decision, "version": updated.version},
                    audit,
                )
            )
            await self.repository.flush()
        return await self._condition_response(updated)

    async def close_conditional_acceptance(
        self, decision_id: UUID, payload: AcceptanceClosureCreate, audit: AuditContext
    ) -> AcceptancePackageResponse:
        async with self.session.begin():
            decision = await self.session.get(AcceptanceDecision, decision_id)
            if decision is None:
                raise ResourceNotFoundError
            package = await self.repository.accessible_package(
                decision.acceptance_package_id, self.actor.user.id, lock=True
            )
            if package is None:
                raise ResourceNotFoundError
            await self._require(package.workspace_id, PermissionCode.ACCEPTANCE_DECIDE)
            if package.employer_recipient_id != self.actor.user.id:
                raise PermissionDeniedError
            existing = await self.repository.closure(decision.id)
            if existing is not None:
                if existing.idempotency_key == payload.idempotency_key:
                    return await self._response(package)
                raise ResourceConflictError
            conditions = await self.repository.conditions(decision.id)
            if (
                decision.decision_kind != "CONDITIONAL_ACCEPT"
                or not conditions
                or any(item.mandatory and item.status != "SATISFIED" for item in conditions)
            ):
                raise ResourceConflictError
            closure = AcceptanceClosure(
                id=uuid4(),
                workspace_id=package.workspace_id,
                decision_id=decision.id,
                actor_id=self.actor.user.id,
                statement=payload.statement,
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([closure])
            self.repository.add_audit_log(
                self._audit(
                    package.workspace_id,
                    "acceptance_closure",
                    closure.id,
                    "CONDITIONAL_ACCEPTANCE_CLOSED",
                    {"decision_id": str(decision.id)},
                    audit,
                )
            )
            await self.repository.flush()
        return await self._response(package)
