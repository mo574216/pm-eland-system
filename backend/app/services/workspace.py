"""Transactional workspace lifecycle and membership policies."""

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
from app.models.identity import AuditLog, Role, User
from app.models.workspace import Workspace, WorkspaceMembership
from app.repositories.workspace import WorkspaceMemberRecord, WorkspaceRepository
from app.services.auth import AuthenticatedIdentity
from app.services.authorization import AuditContext, AuthorizationService


class WorkspaceService:
    """Enforce membership scope, permissions, concurrency, and audit atomically."""

    def __init__(self, session: AsyncSession, actor: AuthenticatedIdentity) -> None:
        self.session = session
        self.actor = actor
        self.authorization = AuthorizationService(actor)
        self.repository = WorkspaceRepository(session)

    def _audit_log(
        self,
        *,
        workspace_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        before_state: dict[str, object] | None,
        after_state: dict[str, object] | None,
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
            before_state=before_state,
            after_state=after_state,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
        )

    async def _require_workspace_permission(
        self, workspace_id: UUID, permission: PermissionCode
    ) -> Workspace:
        workspace = await self.repository.accessible_workspace(workspace_id, self.actor.user.id)
        if workspace is None:
            raise WorkspaceAccessDeniedError
        effective_permissions = self.authorization.permission_codes | frozenset(
            await self.repository.workspace_permission_codes(workspace_id, self.actor.user.id)
        )
        if permission.value not in effective_permissions:
            raise PermissionDeniedError
        return workspace

    async def create_workspace(
        self,
        *,
        name: str,
        slug: str,
        description: str | None,
        audit: AuditContext,
    ) -> Workspace:
        self.authorization.require_permission(PermissionCode.WORKSPACE_CREATE)
        async with self.session.begin():
            if await self.repository.workspace_by_slug(slug) is not None:
                raise ResourceConflictError
            workspace = Workspace(
                id=uuid4(),
                name=name,
                slug=slug,
                description=description,
                owner_id=self.actor.user.id,
                status="DRAFT",
                configuration={},
            )
            membership = WorkspaceMembership(
                id=uuid4(),
                workspace_id=workspace.id,
                user_id=self.actor.user.id,
                role_id=None,
                status="ACTIVE",
            )
            self.repository.add_workspace(workspace)
            self.repository.add_membership(membership)
            self.repository.add_audit_log(
                self._audit_log(
                    workspace_id=workspace.id,
                    action="WORKSPACE_CREATED",
                    resource_type="workspace",
                    resource_id=workspace.id,
                    before_state=None,
                    after_state={"name": name, "slug": slug, "status": "DRAFT"},
                    audit=audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return workspace

    async def list_workspaces(
        self,
        *,
        page: int,
        page_size: int,
        status: str | None,
        search: str | None,
    ) -> tuple[tuple[Workspace, ...], int]:
        return await self.repository.list_accessible_workspaces(
            self.actor.user.id,
            can_read_globally=self.authorization.has_permission(PermissionCode.WORKSPACE_READ),
            page=page,
            page_size=page_size,
            status=status,
            search=search,
        )

    async def get_workspace(self, workspace_id: UUID) -> Workspace:
        return await self._require_workspace_permission(workspace_id, PermissionCode.WORKSPACE_READ)

    async def update_workspace(
        self,
        workspace_id: UUID,
        *,
        expected_version: int,
        values: dict[str, object],
        audit: AuditContext,
    ) -> Workspace:
        async with self.session.begin():
            workspace = await self._require_workspace_permission(
                workspace_id, PermissionCode.WORKSPACE_MANAGE
            )
            before_state: dict[str, object] = {
                "name": workspace.name,
                "description": workspace.description,
                "version": workspace.version,
            }
            updated = await self.repository.update_workspace(workspace_id, expected_version, values)
            if updated is None:
                raise StaleVersionError
            self.repository.add_audit_log(
                self._audit_log(
                    workspace_id=workspace_id,
                    action="WORKSPACE_UPDATED",
                    resource_type="workspace",
                    resource_id=workspace_id,
                    before_state=before_state,
                    after_state={
                        "name": updated.name,
                        "description": updated.description,
                        "version": updated.version,
                    },
                    audit=audit,
                )
            )
        return updated

    async def list_members(self, workspace_id: UUID) -> tuple[WorkspaceMemberRecord, ...]:
        # Project work assigns existing workspace participants by name. Reading this
        # scoped roster does not grant membership administration or directory search.
        await self._require_workspace_permission(workspace_id, PermissionCode.WORKSPACE_READ)
        return await self.repository.list_members(workspace_id)

    async def search_member_candidates(
        self, workspace_id: UUID, *, search: str, limit: int
    ) -> tuple[User, ...]:
        await self._require_workspace_permission(workspace_id, PermissionCode.WORKSPACE_MANAGE)
        return await self.repository.search_member_candidates(workspace_id, search, limit)

    async def list_assignable_roles(self, workspace_id: UUID) -> tuple[Role, ...]:
        await self._require_workspace_permission(workspace_id, PermissionCode.WORKSPACE_MANAGE)
        actor_permissions = self.authorization.permission_codes | frozenset(
            await self.repository.workspace_permission_codes(workspace_id, self.actor.user.id)
        )
        assignable: list[Role] = []
        for role in await self.repository.list_roles():
            role_permissions = set(await self.repository.role_permission_codes(role.id))
            if role_permissions.issubset(actor_permissions):
                assignable.append(role)
        return tuple(assignable)

    async def add_member(
        self,
        workspace_id: UUID,
        *,
        user_id: UUID,
        role_id: UUID,
        audit: AuditContext,
    ) -> WorkspaceMemberRecord:
        async with self.session.begin():
            await self._require_workspace_permission(workspace_id, PermissionCode.WORKSPACE_MANAGE)
            target = await self.repository.user_by_id(user_id)
            role = await self.repository.role_by_id(role_id)
            if target is None or target.is_active is False or role is None:
                raise ResourceNotFoundError
            if await self.repository.membership(workspace_id, user_id) is not None:
                raise ResourceConflictError
            actor_permissions = self.authorization.permission_codes | frozenset(
                await self.repository.workspace_permission_codes(workspace_id, self.actor.user.id)
            )
            role_permissions = set(await self.repository.role_permission_codes(role_id))
            if not role_permissions.issubset(actor_permissions):
                raise PermissionDeniedError

            membership = WorkspaceMembership(
                id=uuid4(),
                workspace_id=workspace_id,
                user_id=user_id,
                role_id=role_id,
                status="ACTIVE",
            )
            self.repository.add_membership(membership)
            self.repository.add_audit_log(
                self._audit_log(
                    workspace_id=workspace_id,
                    action="WORKSPACE_MEMBER_ADDED",
                    resource_type="workspace_membership",
                    resource_id=membership.id,
                    before_state=None,
                    after_state={"user_id": str(user_id), "role_code": role.code},
                    audit=audit,
                )
            )
            try:
                await self.repository.flush()
            except IntegrityError as exc:
                raise ResourceConflictError from exc
        return WorkspaceMemberRecord(
            membership=membership,
            username=target.username,
            display_name=target.display_name,
            role_code=role.code,
        )

    async def remove_member(self, workspace_id: UUID, user_id: UUID, audit: AuditContext) -> None:
        async with self.session.begin():
            await self._require_workspace_permission(workspace_id, PermissionCode.WORKSPACE_MANAGE)
            membership = await self.repository.membership(workspace_id, user_id)
            if membership is None:
                raise ResourceNotFoundError
            removed = await self.repository.remove_membership(membership.id)
            if not removed:
                raise ResourceNotFoundError
            self.repository.add_audit_log(
                self._audit_log(
                    workspace_id=workspace_id,
                    action="WORKSPACE_MEMBER_REMOVED",
                    resource_type="workspace_membership",
                    resource_id=membership.id,
                    before_state={
                        "user_id": str(user_id),
                        "role_id": str(membership.role_id) if membership.role_id else None,
                    },
                    after_state=None,
                    audit=audit,
                )
            )
