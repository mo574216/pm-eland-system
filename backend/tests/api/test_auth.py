# ruff: noqa: S105, S106
"""Authentication endpoint contract tests."""

from typing import cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_auth_service, get_current_identity
from app.core.database import get_database_session
from app.core.exceptions import InvalidCredentialsError
from app.models.identity import User
from app.services.auth import AuthenticatedIdentity, IssuedTokens
from app.services.workspace import WorkspaceService


class SuccessfulAuthService:
    def __init__(self) -> None:
        self.user = User(
            id=uuid4(),
            username="analyst1",
            email="analyst@example.test",
            password_hash="not-returned",
            display_name="Analyst One",
        )

    async def login(self, username: str, password: str) -> IssuedTokens:
        assert username == "analyst1"
        assert password == "valid-password"
        return IssuedTokens(
            access_token="access-token",
            refresh_token="refresh-token",
            identity=AuthenticatedIdentity(self.user, ("ANALYST",), ("ENTITY_READ",)),
        )

    async def refresh(self, raw_refresh_token: str) -> IssuedTokens:
        assert raw_refresh_token == "refresh-token"
        return await self.login("analyst1", "valid-password")

    async def logout(self, raw_refresh_token: str | None) -> None:
        assert raw_refresh_token == "refresh-token"


class RejectingAuthService(SuccessfulAuthService):
    async def login(self, username: str, password: str) -> IssuedTokens:
        raise InvalidCredentialsError


def test_valid_login_returns_bearer_and_secure_refresh_cookie(
    application: FastAPI, client: TestClient
) -> None:
    service = SuccessfulAuthService()
    application.dependency_overrides[get_auth_service] = lambda: service

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst1", "password": "valid-password"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["access_token"] == "access-token"
    assert response.json()["data"]["token_type"] == "bearer"
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=strict" in cookie


def test_invalid_login_uses_safe_generic_error(application: FastAPI, client: TestClient) -> None:
    application.dependency_overrides[get_auth_service] = lambda: RejectingAuthService()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "unknown", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
    assert "unknown" not in response.text


def test_refresh_requires_allowed_origin(application: FastAPI, client: TestClient) -> None:
    application.dependency_overrides[get_auth_service] = lambda: SuccessfulAuthService()
    client.cookies.set("__Host-pm_refresh", "refresh-token")

    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_current_user_resolves_server_side_context(
    application: FastAPI, client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = SuccessfulAuthService()
    identity = AuthenticatedIdentity(service.user, ("ANALYST",), ("ENTITY_READ",))
    application.dependency_overrides[get_current_identity] = lambda: identity

    async def database_override() -> AsyncSession:
        return cast(AsyncSession, object())

    async def list_workspaces(_: WorkspaceService, **__: object) -> tuple[tuple[object, ...], int]:
        return (), 0

    application.dependency_overrides[get_database_session] = database_override
    monkeypatch.setattr(WorkspaceService, "list_workspaces", list_workspaces)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["data"]["roles"] == ["ANALYST"]
    assert response.json()["data"]["permissions"] == ["ENTITY_READ"]
    assert response.json()["data"]["workspaces"] == []
