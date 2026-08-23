"""Safety tests for the development-only administrator bootstrap."""

import pytest

from app.core.config import Settings
from scripts.bootstrap_local_admin import (
    LocalAdminInput,
    bootstrap_local_admin,
    local_admin_input,
)


def test_local_admin_input_requires_explicit_strong_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("LOCAL_ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("LOCAL_ADMIN_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        local_admin_input()


def test_local_admin_input_does_not_supply_a_default_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOCAL_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("LOCAL_ADMIN_EMAIL", "admin@localhost.test")
    monkeypatch.setenv("LOCAL_ADMIN_PASSWORD", "short")

    with pytest.raises(RuntimeError):
        local_admin_input()


@pytest.mark.asyncio
async def test_bootstrap_is_disabled_in_production() -> None:
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        jwt_secret="production-test-secret-at-least-32-characters",  # noqa: S106
        auth_cookie_secure=True,
        storage_access_key="production-test-storage-access",
        storage_secret_key="production-test-storage-secret",  # noqa: S106
    )

    with pytest.raises(RuntimeError, match="disabled in production"):
        await bootstrap_local_admin(
            settings,
            LocalAdminInput("admin", "admin@example.test", "long-test-password"),
        )
