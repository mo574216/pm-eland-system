"""Authentication use cases and session rotation."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationRequiredError, InvalidCredentialsError
from app.core.request_context import get_request_id
from app.core.security import (
    create_access_token,
    create_refresh_token,
    digest_refresh_token,
    verify_password,
)
from app.models.identity import AuthSession, User
from app.repositories.auth import AuthRepository

logger = logging.getLogger("app.auth")


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user: User
    roles: tuple[str, ...]
    permissions: tuple[str, ...]


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    identity: AuthenticatedIdentity


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repository = AuthRepository(session)

    async def login(self, username: str, password: str) -> IssuedTokens:
        now = datetime.now(UTC)
        tokens: IssuedTokens | None = None
        rejected_user_id: UUID | None = None
        async with self.session.begin():
            user = await self.repository.user_by_username(username)
            valid_password = verify_password(password, user.password_hash if user else None)
            if user is None or not valid_password or not user.is_active:
                if user is not None:
                    user.failed_login_count += 1
                    user.updated_at = now
                    rejected_user_id = user.id
            else:
                user.failed_login_count = 0
                user.last_login_at = now
                user.updated_at = now
                tokens = await self._issue(user, now=now, family_id=uuid4())
        if tokens is None:
            logger.warning(
                "login_failed",
                extra={"request_id": get_request_id(), "user_id": rejected_user_id},
            )
            raise InvalidCredentialsError
        logger.info(
            "login_succeeded",
            extra={"request_id": get_request_id(), "user_id": tokens.identity.user.id},
        )
        return tokens

    async def refresh(self, raw_refresh_token: str) -> IssuedTokens:
        now = datetime.now(UTC)
        token_hash = digest_refresh_token(raw_refresh_token)
        tokens: IssuedTokens | None = None
        async with self.session.begin():
            current = await self.repository.auth_session_for_update(token_hash)
            if current is None:
                pass
            elif current.revoked_at is not None:
                await self.repository.revoke_family(current.token_family_id, now)
                logger.warning("refresh_token_reuse", extra={"user_id": current.user_id})
            elif current.expires_at <= now or current.absolute_expires_at <= now:
                current.revoked_at = now
            else:
                user = await self.repository.user_by_id(current.user_id)
                if user is None or not user.is_active:
                    await self.repository.revoke_family(current.token_family_id, now)
                else:
                    tokens = await self._issue(
                        user,
                        now=now,
                        family_id=current.token_family_id,
                        absolute_expires_at=current.absolute_expires_at,
                    )
                    replacement = await self.repository.auth_session_for_update(
                        digest_refresh_token(tokens.refresh_token)
                    )
                    current.revoked_at = now
                    current.last_used_at = now
                    current.replaced_by_id = replacement.id if replacement else None
        if tokens is None:
            raise AuthenticationRequiredError
        return tokens

    async def logout(self, raw_refresh_token: str | None) -> None:
        if raw_refresh_token is None:
            return
        now = datetime.now(UTC)
        async with self.session.begin():
            current = await self.repository.auth_session_for_update(
                digest_refresh_token(raw_refresh_token)
            )
            if current is not None:
                await self.repository.revoke_family(current.token_family_id, now)

    async def identity(self, user_id: UUID) -> AuthenticatedIdentity:
        user = await self.repository.user_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationRequiredError
        return AuthenticatedIdentity(
            user=user,
            roles=await self.repository.role_codes(user_id),
            permissions=await self.repository.permission_codes(user_id),
        )

    async def _issue(
        self,
        user: User,
        *,
        now: datetime,
        family_id: UUID,
        absolute_expires_at: datetime | None = None,
    ) -> IssuedTokens:
        refresh_token = create_refresh_token()
        absolute_expiry = absolute_expires_at or now + timedelta(
            seconds=self.settings.refresh_absolute_expiry_seconds
        )
        idle_expiry = min(
            now + timedelta(seconds=self.settings.refresh_idle_expiry_seconds), absolute_expiry
        )
        auth_session = AuthSession(
            user_id=user.id,
            token_hash=digest_refresh_token(refresh_token),
            token_family_id=family_id,
            expires_at=idle_expiry,
            absolute_expires_at=absolute_expiry,
        )
        self.repository.add_auth_session(auth_session)
        await self.session.flush()
        identity = AuthenticatedIdentity(
            user=user,
            roles=await self.repository.role_codes(user.id),
            permissions=await self.repository.permission_codes(user.id),
        )
        return IssuedTokens(
            access_token=create_access_token(user.id, self.settings, now=now),
            refresh_token=refresh_token,
            identity=identity,
        )
