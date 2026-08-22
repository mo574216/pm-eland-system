"""Identity persistence operations without transaction ownership."""

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import (
    AuditLog,
    AuthSession,
    Permission,
    Role,
    User,
    role_permissions,
    user_roles,
)


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def user_by_username(self, username: str) -> User | None:
        return cast(
            User | None, await self.session.scalar(select(User).where(User.username == username))
        )

    async def user_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def role_codes(self, user_id: UUID) -> tuple[str, ...]:
        statement = (
            select(Role.code)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .order_by(Role.code)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def permission_codes(self, user_id: UUID) -> tuple[str, ...]:
        statement = (
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .distinct()
            .order_by(Permission.code)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def role_by_code(self, role_code: str) -> Role | None:
        return cast(
            Role | None, await self.session.scalar(select(Role).where(Role.code == role_code))
        )

    async def role_permission_codes(self, role_id: UUID) -> tuple[str, ...]:
        statement = (
            select(Permission.code)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
        )
        return tuple((await self.session.scalars(statement)).all())

    async def assign_role(self, user_id: UUID, role_id: UUID) -> bool:
        statement = (
            insert(user_roles)
            .values(user_id=user_id, role_id=role_id)
            .on_conflict_do_nothing()
            .returning(user_roles.c.user_id)
        )
        return (await self.session.scalar(statement)) is not None

    async def remove_role(self, user_id: UUID, role_id: UUID) -> bool:
        result = await self.session.execute(
            delete(user_roles).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id,
            )
        )
        return bool(getattr(result, "rowcount", 0))

    def add_audit_log(self, audit_log: AuditLog) -> None:
        self.session.add(audit_log)

    def add_auth_session(self, auth_session: AuthSession) -> None:
        self.session.add(auth_session)

    async def auth_session_for_update(self, token_hash: str) -> AuthSession | None:
        statement = (
            select(AuthSession).where(AuthSession.token_hash == token_hash).with_for_update()
        )
        return cast(AuthSession | None, await self.session.scalar(statement))

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        await self.session.execute(
            update(AuthSession)
            .where(AuthSession.token_family_id == family_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )
