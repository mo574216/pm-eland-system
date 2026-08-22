"""Workspace persistence operations without transaction ownership."""

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog, Permission, Role, User, role_permissions
from app.models.workspace import Workspace, WorkspaceMembership


@dataclass(frozen=True)
class WorkspaceMemberRecord:
    membership: WorkspaceMembership
    username: str
    display_name: str | None
    role_code: str | None


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_workspace(self, workspace: Workspace) -> None:
        self.session.add(workspace)

    def add_membership(self, membership: WorkspaceMembership) -> None:
        self.session.add(membership)

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    async def flush(self) -> None:
        await self.session.flush()

    async def workspace_by_slug(self, slug: str) -> Workspace | None:
        return cast(
            Workspace | None,
            await self.session.scalar(select(Workspace).where(Workspace.slug == slug)),
        )

    async def accessible_workspace(self, workspace_id: UUID, user_id: UUID) -> Workspace | None:
        statement = (
            select(Workspace)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Workspace.id,
            )
            .where(
                Workspace.id == workspace_id,
                Workspace.deleted_at.is_(None),
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
        )
        return cast(Workspace | None, await self.session.scalar(statement))

    async def workspace_permission_codes(
        self, workspace_id: UUID, user_id: UUID
    ) -> tuple[str, ...]:
        statement = (
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(WorkspaceMembership, WorkspaceMembership.role_id == Role.id)
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "ACTIVE",
            )
            .distinct()
        )
        return tuple((await self.session.scalars(statement)).all())

    async def list_accessible_workspaces(
        self,
        user_id: UUID,
        *,
        can_read_globally: bool,
        page: int,
        page_size: int,
        status: str | None,
        search: str | None,
    ) -> tuple[tuple[Workspace, ...], int]:
        filters = [
            Workspace.deleted_at.is_(None),
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.status == "ACTIVE",
        ]
        statement = select(Workspace).join(
            WorkspaceMembership,
            WorkspaceMembership.workspace_id == Workspace.id,
        )
        count_statement = select(func.count(Workspace.id)).join(
            WorkspaceMembership,
            WorkspaceMembership.workspace_id == Workspace.id,
        )
        if not can_read_globally:
            statement = (
                statement.join(Role, Role.id == WorkspaceMembership.role_id)
                .join(role_permissions, role_permissions.c.role_id == Role.id)
                .join(Permission, Permission.id == role_permissions.c.permission_id)
            )
            count_statement = (
                count_statement.join(Role, Role.id == WorkspaceMembership.role_id)
                .join(role_permissions, role_permissions.c.role_id == Role.id)
                .join(Permission, Permission.id == role_permissions.c.permission_id)
            )
            filters.append(Permission.code == "WORKSPACE_READ")
        if status is not None:
            filters.append(Workspace.status == status)
        if search is not None:
            pattern = f"%{search}%"
            filters.append(or_(Workspace.name.ilike(pattern), Workspace.slug.ilike(pattern)))

        items = tuple(
            (
                await self.session.scalars(
                    statement.where(*filters)
                    .distinct()
                    .order_by(Workspace.name, Workspace.id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
            ).all()
        )
        total = int((await self.session.scalar(count_statement.where(*filters))) or 0)
        return items, total

    async def update_workspace(
        self,
        workspace_id: UUID,
        expected_version: int,
        values: dict[str, object],
    ) -> Workspace | None:
        statement = (
            update(Workspace)
            .where(Workspace.id == workspace_id, Workspace.version == expected_version)
            .values(**values, version=Workspace.version + 1, updated_at=func.now())
            .returning(Workspace)
        )
        return cast(Workspace | None, await self.session.scalar(statement))

    async def user_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def role_by_id(self, role_id: UUID) -> Role | None:
        return await self.session.get(Role, role_id)

    async def role_permission_codes(self, role_id: UUID) -> tuple[str, ...]:
        statement = (
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def membership(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMembership | None:
        statement = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id,
        )
        return cast(WorkspaceMembership | None, await self.session.scalar(statement))

    async def list_members(self, workspace_id: UUID) -> tuple[WorkspaceMemberRecord, ...]:
        statement = (
            select(WorkspaceMembership, User.username, User.display_name, Role.code)
            .join(User, User.id == WorkspaceMembership.user_id)
            .outerjoin(Role, Role.id == WorkspaceMembership.role_id)
            .where(WorkspaceMembership.workspace_id == workspace_id)
            .order_by(User.username)
        )
        rows = (await self.session.execute(statement)).all()
        return tuple(
            WorkspaceMemberRecord(membership, username, display_name, role_code)
            for membership, username, display_name, role_code in rows
        )

    async def remove_membership(self, membership_id: UUID) -> bool:
        result = await self.session.execute(
            delete(WorkspaceMembership).where(WorkspaceMembership.id == membership_id)
        )
        return bool(getattr(result, "rowcount", 0))
