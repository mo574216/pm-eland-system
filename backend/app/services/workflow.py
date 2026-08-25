"""Generic workflow configuration, authorization, and transition policy."""

from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
    StaleVersionError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
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
from app.repositories.workflow import WorkflowRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workflow import (
    WorkflowActionResponse,
    WorkflowDefinitionCreate,
    WorkflowDefinitionResponse,
    WorkflowDefinitionVersionCreate,
    WorkflowInstanceCreate,
    WorkflowInstanceResponse,
    WorkflowStateCreate,
    WorkflowTransitionCreate,
    WorkflowTransitionEventResponse,
    WorkflowTransitionHistoryResponse,
    WorkflowTransitionRequest,
)
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


class WorkflowService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = WorkflowRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

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
        before: dict[str, object] | None,
        after: dict[str, object] | None,
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
            before_state=before,
            after_state=after,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    @staticmethod
    def _graph_records(
        workspace_id: UUID,
        version_id: UUID,
        state_payloads: list[WorkflowStateCreate],
        transition_payloads: list[WorkflowTransitionCreate],
    ) -> tuple[dict[str, WorkflowStateDefinition], list[WorkflowTransitionDefinition]]:
        states = {
            state.key: WorkflowStateDefinition(
                id=uuid4(),
                workspace_id=workspace_id,
                definition_version_id=version_id,
                key=state.key,
                label=state.label,
                sequence_number=state.sequence_number,
                is_initial=state.is_initial,
                is_terminal=state.is_terminal,
                configuration={},
            )
            for state in state_payloads
        }
        transitions = [
            WorkflowTransitionDefinition(
                id=uuid4(),
                workspace_id=workspace_id,
                definition_version_id=version_id,
                key=transition.key,
                label=transition.label,
                from_state_id=states[transition.from_state_key].id,
                to_state_id=states[transition.to_state_key].id,
                required_permission=transition.required_permission.value,
                authority_kind=transition.authority_kind,
                assignment_kind=transition.assignment_kind,
                reason_required=transition.reason_required,
                policy={},
            )
            for transition in transition_payloads
        ]
        return states, transitions

    async def create_definition(
        self, workspace_id: UUID, payload: WorkflowDefinitionCreate, audit: AuditContext
    ) -> WorkflowDefinitionResponse:
        async with self.session.begin():
            await self._require(workspace_id, PermissionCode.WORKFLOW_CONFIGURE)
            key = payload.key or f"workflow_{uuid4().hex}"
            if await self.repository.definition_by_key(workspace_id, key) is not None:
                raise ResourceConflictError
            definition = WorkflowDefinition(
                id=uuid4(),
                workspace_id=workspace_id,
                key=key,
                name=payload.name,
                description=payload.description,
                created_by=self.actor.user.id,
                version=1,
            )
            version = WorkflowDefinitionVersion(
                id=uuid4(),
                workspace_id=workspace_id,
                definition_id=definition.id,
                version_number=1,
                status="DRAFT",
                configuration={},
                created_by=self.actor.user.id,
            )
            states, transitions = self._graph_records(
                workspace_id, version.id, payload.states, payload.transitions
            )
            self.repository.add_all([definition, version, *states.values(), *transitions])
            self.repository.add_audit_log(
                self._audit(
                    workspace_id,
                    "workflow_definition",
                    definition.id,
                    "WORKFLOW_DEFINITION_CREATED",
                    None,
                    {"key": key, "version_number": 1, "status": "DRAFT"},
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return WorkflowDefinitionResponse(
            id=definition.id,
            workspace_id=workspace_id,
            key=definition.key,
            name=definition.name,
            description=definition.description,
            version=definition.version,
            definition_version_id=version.id,
            definition_version_number=version.version_number,
            status=version.status,
        )

    async def create_definition_version(
        self,
        definition_id: UUID,
        payload: WorkflowDefinitionVersionCreate,
        audit: AuditContext,
    ) -> WorkflowDefinitionResponse:
        async with self.session.begin():
            definition = await self.repository.accessible_definition(
                definition_id, self.actor.user.id, lock=True
            )
            if definition is None:
                raise ResourceNotFoundError
            await self._require(definition.workspace_id, PermissionCode.WORKFLOW_CONFIGURE)
            updated_definition = await self.repository.bump_definition(
                definition.id, payload.expected_version
            )
            if updated_definition is None:
                raise StaleVersionError
            version_number = await self.repository.next_version_number(definition.id)
            version = WorkflowDefinitionVersion(
                id=uuid4(),
                workspace_id=definition.workspace_id,
                definition_id=definition.id,
                version_number=version_number,
                status="DRAFT",
                configuration={},
                created_by=self.actor.user.id,
            )
            states, transitions = self._graph_records(
                definition.workspace_id, version.id, payload.states, payload.transitions
            )
            self.repository.add_all([version, *states.values(), *transitions])
            self.repository.add_audit_log(
                self._audit(
                    definition.workspace_id,
                    "workflow_definition",
                    definition.id,
                    "WORKFLOW_DEFINITION_VERSION_CREATED",
                    {"definition_version": version_number - 1},
                    {"definition_version": version_number, "status": "DRAFT"},
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return WorkflowDefinitionResponse(
            id=updated_definition.id,
            workspace_id=updated_definition.workspace_id,
            key=updated_definition.key,
            name=updated_definition.name,
            description=updated_definition.description,
            version=updated_definition.version,
            definition_version_id=version.id,
            definition_version_number=version.version_number,
            status=version.status,
        )

    async def publish_version(
        self, version_id: UUID, *, audit: AuditContext
    ) -> WorkflowDefinitionResponse:
        async with self.session.begin():
            version = await self.repository.version(version_id)
            if version is None:
                raise ResourceNotFoundError
            definition = await self.repository.accessible_definition(
                version.definition_id, self.actor.user.id, lock=True
            )
            if definition is None or definition.workspace_id != version.workspace_id:
                raise ResourceNotFoundError
            await self._require(version.workspace_id, PermissionCode.WORKFLOW_CONFIGURE)
            published = await self.repository.publish_version(
                version.id, actor_id=self.actor.user.id
            )
            if published is None:
                raise ResourceConflictError
            self.repository.add_audit_log(
                self._audit(
                    version.workspace_id,
                    "workflow_definition",
                    definition.id,
                    "WORKFLOW_DEFINITION_PUBLISHED",
                    {"status": "DRAFT", "version_number": version.version_number},
                    {"status": "PUBLISHED", "version_number": version.version_number},
                    audit,
                )
            )
        return WorkflowDefinitionResponse(
            id=definition.id,
            workspace_id=definition.workspace_id,
            key=definition.key,
            name=definition.name,
            description=definition.description,
            version=definition.version,
            definition_version_id=published.id,
            definition_version_number=published.version_number,
            status=published.status,
        )

    async def start_instance(
        self, workspace_id: UUID, payload: WorkflowInstanceCreate, audit: AuditContext
    ) -> WorkflowInstanceResponse:
        async with self.session.begin():
            await self._require(workspace_id, PermissionCode.WORKFLOW_CONFIGURE)
            version = await self.repository.version(payload.definition_version_id)
            if (
                version is None
                or version.workspace_id != workspace_id
                or version.status != "PUBLISHED"
            ):
                raise ResourceNotFoundError
            definition = await self.repository.accessible_definition(
                version.definition_id, self.actor.user.id
            )
            if definition is None:
                raise ResourceNotFoundError
            if not await self.repository.target_in_workspace(
                workspace_id, payload.target_kind, payload.target_id
            ):
                raise ResourceNotFoundError
            member_ids = {assignment.user_id for assignment in payload.assignments}
            if await self.repository.active_members(workspace_id, member_ids) != member_ids:
                raise ResourceNotFoundError
            initial = await self.repository.initial_state(version.id)
            if initial is None:
                raise ResourceConflictError
            instance = WorkflowInstance(
                id=uuid4(),
                workspace_id=workspace_id,
                definition_version_id=version.id,
                current_state_id=initial.id,
                target_kind=payload.target_kind,
                target_id=payload.target_id,
                target_version=payload.target_version,
                started_by=self.actor.user.id,
                version=1,
            )
            assignments = [
                WorkflowAssignment(
                    id=uuid4(),
                    workspace_id=workspace_id,
                    instance_id=instance.id,
                    user_id=assignment.user_id,
                    assignment_kind=assignment.assignment_kind,
                    assigned_by=self.actor.user.id,
                )
                for assignment in payload.assignments
            ]
            event = WorkflowTransitionEvent(
                id=uuid4(),
                workspace_id=workspace_id,
                instance_id=instance.id,
                transition_id=None,
                definition_version_id=version.id,
                previous_state_id=None,
                resulting_state_id=initial.id,
                action_key="START",
                authority_kind="CONFIGURATION",
                actor_id=self.actor.user.id,
                target_version=payload.target_version,
                resulting_instance_version=1,
                reason=None,
                context={},
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add_all([instance, *assignments, event])
            self.repository.add_audit_log(
                self._audit(
                    workspace_id,
                    "workflow_instance",
                    instance.id,
                    "WORKFLOW_INSTANCE_STARTED",
                    None,
                    {"state": initial.key, "target_kind": payload.target_kind},
                    audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return await self._instance_response(instance, version.version_number, initial)

    async def get_instance(self, instance_id: UUID) -> WorkflowInstanceResponse:
        instance = await self.repository.accessible_instance(instance_id, self.actor.user.id)
        if instance is None:
            raise ResourceNotFoundError
        await self._require(instance.workspace_id, PermissionCode.WORKSPACE_READ)
        version = await self.repository.version(instance.definition_version_id)
        state = await self.repository.state(instance.current_state_id)
        if version is None or state is None:
            raise ResourceNotFoundError
        return await self._instance_response(instance, version.version_number, state)

    async def transition_history(
        self, instance_id: UUID, *, page: int, page_size: int
    ) -> WorkflowTransitionHistoryResponse:
        instance = await self.repository.accessible_instance(instance_id, self.actor.user.id)
        if instance is None:
            raise ResourceNotFoundError
        await self._require(instance.workspace_id, PermissionCode.WORKSPACE_READ)
        events, total = await self.repository.history(instance.id, page=page, page_size=page_size)
        state_ids = {
            state_id
            for event in events
            for state_id in (event.previous_state_id, event.resulting_state_id)
            if state_id is not None
        }
        states = await self.repository.states(state_ids)
        return WorkflowTransitionHistoryResponse(
            items=[
                WorkflowTransitionEventResponse(
                    id=event.id,
                    action_key=event.action_key,
                    authority_kind=event.authority_kind,
                    previous_state_key=(
                        states[event.previous_state_id].key
                        if event.previous_state_id is not None
                        else None
                    ),
                    resulting_state_key=states[event.resulting_state_id].key,
                    actor_id=event.actor_id,
                    target_version=event.target_version,
                    resulting_instance_version=event.resulting_instance_version,
                    reason=event.reason,
                    occurred_at=event.occurred_at,
                )
                for event in events
            ],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def transition_instance(
        self,
        instance_id: UUID,
        action_key: str,
        payload: WorkflowTransitionRequest,
        audit: AuditContext,
    ) -> WorkflowInstanceResponse:
        transaction = (
            self.session.begin_nested() if self.session.in_transaction() else self.session.begin()
        )
        async with transaction:
            instance = await self.repository.accessible_instance(
                instance_id, self.actor.user.id, lock=True
            )
            if instance is None:
                raise ResourceNotFoundError
            existing = await self.repository.event_by_idempotency(
                instance.id, payload.idempotency_key
            )
            if existing is not None:
                if existing.action_key != action_key:
                    raise ResourceConflictError
                version = await self.repository.version(instance.definition_version_id)
                state = await self.repository.state(instance.current_state_id)
                if version is None or state is None:
                    raise ResourceNotFoundError
                return await self._instance_response(instance, version.version_number, state)
            transition = await self.repository.transition(
                instance.definition_version_id, instance.current_state_id, action_key
            )
            if transition is None:
                raise ResourceConflictError
            effective = await self._effective_permissions(instance.workspace_id)
            if transition.required_permission not in effective:
                raise PermissionDeniedError
            if transition.assignment_kind is not None and not await self.repository.has_assignment(
                instance.id, self.actor.user.id, transition.assignment_kind
            ):
                raise PermissionDeniedError
            if transition.reason_required and not payload.reason:
                raise ResourceConflictError
            if transition.policy.get("requires_package_readiness"):
                if (
                    instance.target_kind != "DELIVERABLE"
                    or not await self.repository.deliverable_package_is_ready(instance.target_id)
                ):
                    raise ResourceConflictError
            if transition.policy.get("requires_active_submission"):
                if (
                    instance.target_kind != "DELIVERABLE"
                    or not await self.repository.has_active_submission_version(
                        instance.target_id, payload.target_version
                    )
                ):
                    raise ResourceConflictError
            if transition.policy.get("requires_submission_withdrawal"):
                if (
                    instance.target_kind != "DELIVERABLE"
                    or not await self.repository.latest_submission_is_withdrawn(instance.target_id)
                ):
                    raise ResourceConflictError
            previous_state = await self.repository.state(instance.current_state_id)
            resulting_state = await self.repository.state(transition.to_state_id)
            version = await self.repository.version(instance.definition_version_id)
            if previous_state is None or resulting_state is None or version is None:
                raise ResourceNotFoundError
            updated = await self.repository.update_instance_state(
                instance.id,
                payload.expected_version,
                transition.to_state_id,
                payload.target_version,
            )
            if updated is None:
                raise StaleVersionError
            event = WorkflowTransitionEvent(
                id=uuid4(),
                workspace_id=instance.workspace_id,
                instance_id=instance.id,
                transition_id=transition.id,
                definition_version_id=instance.definition_version_id,
                previous_state_id=previous_state.id,
                resulting_state_id=resulting_state.id,
                action_key=transition.key,
                authority_kind=transition.authority_kind,
                actor_id=self.actor.user.id,
                target_version=payload.target_version or updated.target_version,
                resulting_instance_version=updated.version,
                reason=payload.reason,
                context={"required_permission": transition.required_permission},
                idempotency_key=payload.idempotency_key,
            )
            self.repository.add(event)
            self.repository.add_audit_log(
                self._audit(
                    instance.workspace_id,
                    "workflow_instance",
                    instance.id,
                    "WORKFLOW_TRANSITIONED",
                    {"state": previous_state.key, "version": payload.expected_version},
                    {
                        "state": resulting_state.key,
                        "version": updated.version,
                        "action": transition.key,
                        "authority_kind": transition.authority_kind,
                    },
                    audit,
                )
            )
        return await self._instance_response(updated, version.version_number, resulting_state)

    async def _instance_response(
        self,
        instance: WorkflowInstance,
        definition_version_number: int,
        state: WorkflowStateDefinition,
    ) -> WorkflowInstanceResponse:
        effective = await self._effective_permissions(instance.workspace_id)
        actions: list[WorkflowActionResponse] = []
        for transition in await self.repository.transitions_from(
            instance.definition_version_id, instance.current_state_id
        ):
            if transition.required_permission not in effective:
                continue
            if transition.assignment_kind is not None and not await self.repository.has_assignment(
                instance.id, self.actor.user.id, transition.assignment_kind
            ):
                continue
            if transition.policy.get("requires_package_readiness") and (
                instance.target_kind != "DELIVERABLE"
                or not await self.repository.deliverable_package_is_ready(instance.target_id)
            ):
                continue
            actions.append(
                WorkflowActionResponse(
                    key=transition.key,
                    label=transition.label,
                    authority_kind=transition.authority_kind,
                    reason_required=transition.reason_required,
                )
            )
        return WorkflowInstanceResponse(
            id=instance.id,
            workspace_id=instance.workspace_id,
            definition_version_id=instance.definition_version_id,
            definition_version_number=definition_version_number,
            target_kind=instance.target_kind,
            target_id=instance.target_id,
            target_version=instance.target_version,
            current_state_key=state.key,
            current_state_label=state.label,
            version=instance.version,
            available_actions=actions,
        )
