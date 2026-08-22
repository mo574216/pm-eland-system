"""Password and token primitives for the approved session architecture."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

password_hash = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = password_hash.hash("authentication-timing-placeholder")


class AccessTokenExpiredError(ValueError):
    """The access token was otherwise valid but has expired."""


class InvalidAccessTokenError(ValueError):
    """The access token is malformed or fails required validation."""


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    return password_hash.verify(password, encoded_hash or _DUMMY_PASSWORD_HASH)


def _jwt_secret(settings: Settings) -> str:
    if settings.jwt_secret is None:
        raise RuntimeError("JWT_SECRET is required for authentication operations.")
    return settings.jwt_secret.get_secret_value()


def create_access_token(user_id: UUID, settings: Settings, *, now: datetime | None = None) -> str:
    issued_at = now or datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "jti": str(uuid4()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=settings.jwt_expiry_seconds),
    }
    return jwt.encode(claims, _jwt_secret(settings), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        claims = jwt.decode(
            token,
            _jwt_secret(settings),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "jti", "iss", "aud", "iat", "exp"]},
        )
        return UUID(claims["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise AccessTokenExpiredError from exc
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise InvalidAccessTokenError from exc


def create_refresh_token() -> str:
    return token_urlsafe(48)


def digest_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
