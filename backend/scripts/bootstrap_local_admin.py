"""Create an explicit development-only system administrator without overwriting users."""

import asyncio
import sys
from dataclasses import dataclass
from os import environ
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import Settings
from app.core.database import create_database_engine, create_session_factory
from app.core.security import hash_password
from app.models.identity import AuditLog, Role, User, user_roles


@dataclass(frozen=True)
class LocalAdminInput:
    username: str
    email: str
    password: str


def local_admin_input() -> LocalAdminInput:
    username = environ.get("LOCAL_ADMIN_USERNAME", "").strip()
    email = environ.get("LOCAL_ADMIN_EMAIL", "").strip()
    password = environ.get("LOCAL_ADMIN_PASSWORD", "")
    if not username or not email or len(password) < 12:
        raise RuntimeError(
            "LOCAL_ADMIN_USERNAME, LOCAL_ADMIN_EMAIL, and a password of at least "
            "12 characters are required."
        )
    return LocalAdminInput(username, email, password)


async def bootstrap_local_admin(settings: Settings, values: LocalAdminInput) -> bool:
    if settings.app_env.lower() == "production":
        raise RuntimeError("Local administrator bootstrap is disabled in production.")
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required.")
    engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    created = False
    try:
        async with session_factory() as session, session.begin():
            user = await session.scalar(
                select(User).where(
                    (User.username == values.username) | (User.email == values.email)
                )
            )
            if user is not None and (
                str(user.username).lower() != values.username.lower()
                or str(user.email).lower() != values.email.lower()
            ):
                raise RuntimeError("Username or email belongs to a different local user.")
            if user is None:
                user = User(
                    id=uuid4(),
                    username=values.username,
                    email=values.email,
                    password_hash=hash_password(values.password),
                    display_name="Local System Administrator",
                    is_active=True,
                    failed_login_count=0,
                    version=1,
                )
                session.add(user)
                await session.flush()
                created = True
            role = await session.scalar(select(Role).where(Role.code == "SYSTEM_ADMIN"))
            if role is None:
                raise RuntimeError("SYSTEM_ADMIN seed is missing; run migrations first.")
            assignment = await session.execute(
                insert(user_roles).values(user_id=user.id, role_id=role.id).on_conflict_do_nothing()
            )
            assigned = bool(getattr(assignment, "rowcount", 0))
            if created or assigned:
                session.add(
                    AuditLog(
                        id=uuid4(),
                        request_id=uuid4(),
                        user_id=user.id,
                        action="LOCAL_ADMIN_BOOTSTRAPPED",
                        resource_type="user",
                        resource_id=user.id,
                        source="SYSTEM",
                        before_state=None,
                        after_state={
                            "username": values.username,
                            "role_code": "SYSTEM_ADMIN",
                        },
                    )
                )
    finally:
        await engine.dispose()
    return created


async def async_main() -> None:
    created = await bootstrap_local_admin(Settings(), local_admin_input())
    print("Local administrator created." if created else "Local administrator already exists.")


def main() -> None:
    if sys.platform == "win32":
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(async_main())
        return
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
