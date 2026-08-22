# ruff: noqa: S105, S106
"""Authentication cryptography tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    digest_refresh_token,
    hash_password,
    verify_password,
)


def auth_settings() -> Settings:
    return Settings(jwt_secret="a-test-secret-with-at-least-32-characters")


def test_passwords_use_argon2id_and_verify_securely() -> None:
    encoded = hash_password("correct horse battery staple")

    assert encoded.startswith("$argon2id$")
    assert verify_password("correct horse battery staple", encoded) is True
    assert verify_password("wrong", encoded) is False
    assert verify_password("wrong", None) is False


def test_access_token_contains_and_validates_minimal_identity() -> None:
    user_id = uuid4()
    token = create_access_token(user_id, auth_settings())

    assert decode_access_token(token, auth_settings()) == user_id


def test_expired_access_token_is_distinguished() -> None:
    token = create_access_token(
        uuid4(), auth_settings(), now=datetime.now(UTC) - timedelta(hours=1)
    )

    with pytest.raises(AccessTokenExpiredError):
        decode_access_token(token, auth_settings())


def test_access_token_rejects_wrong_signing_secret() -> None:
    token = create_access_token(uuid4(), auth_settings())
    other_settings = Settings(jwt_secret="a-different-secret-with-at-least-32-chars")

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, other_settings)


def test_refresh_token_digest_does_not_retain_raw_token() -> None:
    raw_token = "opaque-refresh-token"
    digest = digest_refresh_token(raw_token)

    assert digest != raw_token
    assert len(digest) == 64


def test_production_rejects_missing_secret_or_insecure_cookie() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production")
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret="a-production-secret-with-at-least-32-characters",
            auth_cookie_secure=False,
        )
