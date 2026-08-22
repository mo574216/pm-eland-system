# ruff: noqa: S105, S106
"""Authentication service behavior tests."""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationRequiredError, InvalidCredentialsError
from app.core.security import digest_refresh_token, hash_password
from app.models.identity import AuthSession, User
from app.repositories.auth import AuthRepository
from app.services.auth import AuthService


class TransactionContext:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: object) -> None:
        return None


class FakeSession:
    def begin(self) -> TransactionContext:
        return TransactionContext()

    async def flush(self) -> None:
        return None


class FakeRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user
        self.sessions: dict[str, AuthSession] = {}
        self.revoked_families: list[UUID] = []

    async def user_by_username(self, _: str) -> User | None:
        return self.user

    async def user_by_id(self, _: UUID) -> User | None:
        return self.user

    async def role_codes(self, _: UUID) -> tuple[str, ...]:
        return ("ANALYST",)

    async def permission_codes(self, _: UUID) -> tuple[str, ...]:
        return ("ENTITY_READ",)

    def add_auth_session(self, auth_session: AuthSession) -> None:
        self.sessions[auth_session.token_hash] = auth_session

    async def auth_session_for_update(self, token_hash: str) -> AuthSession | None:
        return self.sessions.get(token_hash)

    async def revoke_family(self, family_id: UUID, revoked_at: datetime) -> None:
        self.revoked_families.append(family_id)
        for auth_session in self.sessions.values():
            if auth_session.token_family_id == family_id and auth_session.revoked_at is None:
                auth_session.revoked_at = revoked_at


def settings() -> Settings:
    return Settings(jwt_secret="a-test-secret-with-at-least-32-characters")


def user(*, active: bool = True) -> User:
    return User(
        id=uuid4(),
        username="analyst1",
        email="analyst@example.test",
        password_hash=hash_password("valid-password"),
        display_name="Analyst One",
        is_active=active,
        failed_login_count=0,
    )


def service_with(repository: FakeRepository) -> AuthService:
    service = AuthService(cast(AsyncSession, FakeSession()), settings())
    service.repository = cast(AuthRepository, repository)
    return service


@pytest.mark.asyncio
async def test_auth_fr_001_valid_login() -> None:
    repository = FakeRepository(user())

    tokens = await service_with(repository).login("analyst1", "valid-password")

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.identity.roles == ("ANALYST",)
    assert repository.user is not None
    assert repository.user.failed_login_count == 0
    assert repository.user.last_login_at is not None
    assert len(repository.sessions) == 1


@pytest.mark.asyncio
async def test_invalid_password_is_generic_and_tracks_failure() -> None:
    repository = FakeRepository(user())

    with pytest.raises(InvalidCredentialsError):
        await service_with(repository).login("analyst1", "wrong-password")

    assert repository.user is not None
    assert repository.user.failed_login_count == 1


@pytest.mark.asyncio
async def test_inactive_user_is_rejected() -> None:
    repository = FakeRepository(user(active=False))

    with pytest.raises(InvalidCredentialsError):
        await service_with(repository).login("analyst1", "valid-password")

    assert repository.sessions == {}


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_reuse_revokes_family() -> None:
    active_user = user()
    repository = FakeRepository(active_user)
    family_id = uuid4()
    raw_token = "original-refresh-token"
    original = AuthSession(
        id=uuid4(),
        user_id=active_user.id,
        token_hash=digest_refresh_token(raw_token),
        token_family_id=family_id,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        absolute_expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    repository.add_auth_session(original)
    service = service_with(repository)

    replacement = await service.refresh(raw_token)

    assert replacement.refresh_token != raw_token
    assert original.revoked_at is not None
    assert len(repository.sessions) == 2

    with pytest.raises(AuthenticationRequiredError):
        await service.refresh(raw_token)

    assert repository.revoked_families == [family_id]
