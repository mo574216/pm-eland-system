"""Phase lifecycle, workspace isolation, lock policy, and audit services."""

from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PermissionDeniedError,
    ResourceConflictError,
    ResourceLockedError,
    ResourceNotFoundError,
    StaleVersionError,
    WorkspaceAccessDeniedError,
)
from app.core.permissions import PermissionCode
from app.models.identity import AuditLog
from app.models.phase import Phase
from app.repositories.phase import PhaseRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


class PhaseService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = PhaseRepository(session)
        self.workspace_repository = WorkspaceRepository(session)

    async def _require(self, workspace_id: UUID, permission: PermissionCode) -> None:
        workspace = await self.workspace_repository.accessible_workspace(
            workspace_id, self.actor.user.id
        )
        if workspace is None:
            raise WorkspaceAccessDeniedError
        effective = self.authorization.permission_codes | frozenset(
            await self.workspace_repository.workspace_permission_codes(
                workspace_id, self.actor.user.id
            )
        )
        if permission.value not in effective:
            raise PermissionDeniedError

    @staticmethod
    def _state(phase: Phase) -> dict[str, object]:
        return {
            "name": phase.name,
            "sequence_number": phase.sequence_number,
            "status": phase.status,
            "is_locked": phase.is_locked,
            "version": phase.version,
        }

    def _audit(
        self,
        phase: Phase,
        action: str,
        before: dict[str, object] | None,
        after: dict[str, object] | None,
        context: AuditContext,
    ) -> AuditLog:
        return AuditLog(
            id=uuid4(),
            request_id=context.request_id,
            workspace_id=phase.workspace_id,
            user_id=self.actor.user.id,
            action=action,
            resource_type="phase",
            resource_id=phase.id,
            before_state=before,
            after_state=after,
            client_ip=context.client_ip,
            user_agent=context.user_agent,
        )

    async def create_phase(
        self, workspace_id: UUID, *, values: dict[str, object], audit: AuditContext
    ) -> Phase:
        async with self.session.begin():
            await self._require(workspace_id, PermissionCode.PHASE_MANAGE)
            if values.get("key") is None:
                values["key"] = f"phase_{uuid4().hex}"
            if await self.repository.by_key(workspace_id, str(values["key"])) is not None:
                raise ResourceConflictError
            phase = Phase(
                id=uuid4(),
                workspace_id=workspace_id,
                status="PLANNED",
                is_locked=False,
                version=1,
                **values,
            )
            self.repository.add_phase(phase)
            self.repository.add_audit_log(
                self._audit(phase, "PHASE_CREATED", None, self._state(phase), audit)
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return phase

    async def list_phases(self, workspace_id: UUID) -> tuple[Phase, ...]:
        await self._require(workspace_id, PermissionCode.WORKSPACE_READ)
        return await self.repository.list_phases(workspace_id, self.actor.user.id)

    async def update_phase(
        self,
        phase_id: UUID,
        *,
        expected_version: int,
        values: dict[str, object],
        audit: AuditContext,
    ) -> Phase:
        async with self.session.begin():
            phase = await self.repository.accessible_phase(phase_id, self.actor.user.id, lock=True)
            if phase is None:
                raise ResourceNotFoundError
            await self._require(phase.workspace_id, PermissionCode.PHASE_MANAGE)
            if phase.is_locked:
                raise ResourceLockedError
            before = self._state(phase)
            updated = await self.repository.update_phase(phase_id, expected_version, values)
            if updated is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._audit(updated, "PHASE_UPDATED", before, self._state(updated), audit)
            )
        return updated

    async def set_locked(self, phase_id: UUID, *, locked: bool, audit: AuditContext) -> Phase:
        async with self.session.begin():
            phase = await self.repository.accessible_phase(phase_id, self.actor.user.id, lock=True)
            if phase is None:
                raise ResourceNotFoundError
            await self._require(
                phase.workspace_id,
                PermissionCode.PHASE_LOCK if locked else PermissionCode.PHASE_UNLOCK,
            )
            if phase.is_locked == locked:
                return phase
            before = self._state(phase)
            updated = await self.repository.set_lock(
                phase_id, locked=locked, actor_id=self.actor.user.id
            )
            if updated is None:
                raise ResourceNotFoundError
            action = "PHASE_LOCKED" if locked else "PHASE_UNLOCKED"
            self.repository.add_audit_log(
                self._audit(updated, action, before, self._state(updated), audit)
            )
        return updated


class LockPolicyService:
    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.actor = actor
        self.repository = PhaseRepository(session)

    async def assert_phase_mutable(self, phase_id: UUID) -> Phase:
        phase = await self.repository.accessible_phase(phase_id, self.actor.user.id)
        if phase is None:
            raise ResourceNotFoundError
        if phase.is_locked:
            raise ResourceLockedError
        return phase
