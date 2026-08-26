"""Opt-in local-only personas for the governed-delivery MVP walkthrough.

The caller supplies the password at runtime. This script never prints, stores in
source, or overwrites a password. It is deliberately not a production seeder.
"""

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
from app.models.workspace import Workspace, WorkspaceMembership


@dataclass(frozen=True)
class DemoInput:
    workspace_name: str
    password: str


DEMO_PERSONAS: tuple[tuple[str, str, str, str], ...] = (
    ("demo_manager", "demo.manager@example.test", "مدیر پروژه نمونه", "PROJECT_MANAGER"),
    (
        "demo_leader",
        "demo.leader@example.test",
        "رهبر پیمانکار نمونه",
        "CONTRACTOR_PROJECT_LEADER",
    ),
    (
        "demo_reviewer",
        "demo.reviewer@example.test",
        "بازبین فنی نمونه",
        "TECHNICAL_REVIEWER",
    ),
    (
        "demo_employer",
        "demo.employer@example.test",
        "نماینده کارفرما نمونه",
        "EMPLOYER_REPRESENTATIVE",
    ),
)


def demo_input() -> DemoInput:
    workspace_name = environ.get("DEMO_WORKSPACE_NAME", "").strip()
    password = environ.get("DEMO_PASSWORD", "")
    if not workspace_name:
        raise RuntimeError("DEMO_WORKSPACE_NAME is required.")
    if len(password) < 12:
        raise RuntimeError("DEMO_PASSWORD must contain at least 12 characters.")
    return DemoInput(workspace_name=workspace_name, password=password)


async def bootstrap_demo_personas(settings: Settings, values: DemoInput) -> tuple[str, ...]:
    if settings.app_env.lower() == "production":
        raise RuntimeError("Demo persona bootstrap is disabled in production.")
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required.")
    engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    usernames: list[str] = []
    try:
        async with session_factory() as session, session.begin():
            workspaces = (
                await session.scalars(
                    select(Workspace).where(
                        Workspace.name == values.workspace_name,
                        Workspace.deleted_at.is_(None),
                    )
                )
            ).all()
            if len(workspaces) != 1:
                raise RuntimeError(
                    "DEMO_WORKSPACE_NAME must identify exactly one non-deleted workspace."
                )
            workspace = workspaces[0]
            role_codes = {item[3] for item in DEMO_PERSONAS}
            roles = {
                value.code: value
                for value in (
                    await session.scalars(select(Role).where(Role.code.in_(role_codes)))
                ).all()
            }
            if set(roles) != role_codes:
                raise RuntimeError("Required baseline role seed is missing; run migrations first.")
            for username, email, display_name, role_code in DEMO_PERSONAS:
                user = await session.scalar(select(User).where(User.username == username))
                created = user is None
                if user is None:
                    user = User(
                        id=uuid4(),
                        username=username,
                        email=email,
                        display_name=display_name,
                        password_hash=hash_password(values.password),
                        is_active=True,
                        failed_login_count=0,
                        version=1,
                    )
                    session.add(user)
                    await session.flush()
                elif user.email.lower() != email.lower():
                    raise RuntimeError(f"Demo username '{username}' belongs to a different user.")
                role = roles[role_code]
                await session.execute(
                    insert(user_roles)
                    .values(user_id=user.id, role_id=role.id)
                    .on_conflict_do_nothing()
                )
                membership = await session.scalar(
                    select(WorkspaceMembership).where(
                        WorkspaceMembership.workspace_id == workspace.id,
                        WorkspaceMembership.user_id == user.id,
                    )
                )
                membership_created = membership is None
                if membership is None:
                    session.add(
                        WorkspaceMembership(
                            id=uuid4(),
                            workspace_id=workspace.id,
                            user_id=user.id,
                            role_id=role.id,
                            status="ACTIVE",
                        )
                    )
                if created or membership_created:
                    session.add(
                        AuditLog(
                            id=uuid4(),
                            request_id=uuid4(),
                            workspace_id=workspace.id,
                            user_id=user.id,
                            action="DEMO_PERSONA_BOOTSTRAPPED",
                            resource_type="workspace_membership",
                            resource_id=user.id,
                            source="SYSTEM",
                            before_state=None,
                            after_state={"username": username, "role_code": role_code},
                        )
                    )
                usernames.append(username)
    finally:
        await engine.dispose()
    return tuple(usernames)


async def async_main() -> None:
    usernames = await bootstrap_demo_personas(Settings(), demo_input())
    print("Demo personas ready: " + ", ".join(usernames))


def main() -> None:
    if sys.platform == "win32":
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(async_main())
        return
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
