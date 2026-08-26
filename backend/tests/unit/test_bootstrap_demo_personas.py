"""Safety contracts for opt-in local demo personas."""

import pytest

from app.core.config import Settings
from scripts.bootstrap_demo_personas import (
    DEMO_PERSONAS,
    DemoInput,
    bootstrap_demo_personas,
    demo_input,
)


def test_demo_personas_cover_the_required_governed_handoff_lanes() -> None:
    assert {item[3] for item in DEMO_PERSONAS} == {
        "PROJECT_MANAGER",
        "CONTRACTOR_PROJECT_LEADER",
        "TECHNICAL_REVIEWER",
        "EMPLOYER_REPRESENTATIVE",
    }


def test_demo_input_requires_named_scope_and_strong_runtime_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEMO_WORKSPACE_NAME", raising=False)
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        demo_input()

    monkeypatch.setenv("DEMO_WORKSPACE_NAME", "Demo")
    monkeypatch.setenv("DEMO_PASSWORD", "short")
    with pytest.raises(RuntimeError):
        demo_input()


@pytest.mark.asyncio
async def test_demo_personas_are_disabled_in_production() -> None:
    settings = Settings(
        app_env="production",
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        jwt_secret="production-test-secret-at-least-32-characters",  # noqa: S106
        auth_cookie_secure=True,
        storage_access_key="production-test-storage-access",
        storage_secret_key="production-test-storage-secret",  # noqa: S106
    )
    with pytest.raises(RuntimeError, match="disabled in production"):
        await bootstrap_demo_personas(settings, DemoInput("Demo", "long-test-password"))
