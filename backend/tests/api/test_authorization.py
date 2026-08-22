"""Server-side permission dependency tests."""

from typing import Annotated, cast
from uuid import uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_current_identity
from app.api.dependencies.authorization import require_permission
from app.core.database import get_database_session
from app.core.permissions import PermissionCode
from app.models.identity import User
from app.services.auth import AuthenticatedIdentity


def identity(permission: PermissionCode) -> AuthenticatedIdentity:
    user = User(
        id=uuid4(),
        username="designer",
        email="designer@example.test",
        password_hash="unused-in-authorization-test",  # noqa: S106
        display_name="Form Designer",
    )
    return AuthenticatedIdentity(user, ("ANALYST",), (permission.value,))


def install_protected_endpoint(application: FastAPI) -> None:
    permission_dependency = require_permission(PermissionCode.FORM_DESIGN)

    @application.get("/test-only/protected")
    async def protected(
        _: Annotated[AuthenticatedIdentity, Depends(permission_dependency)],
    ) -> dict[str, bool]:
        return {"allowed": True}


def test_direct_api_request_rejects_missing_permission(
    application: FastAPI, client: TestClient
) -> None:
    install_protected_endpoint(application)
    application.dependency_overrides[get_current_identity] = lambda: identity(
        PermissionCode.ENTITY_READ
    )

    response = client.get("/test-only/protected")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_elevated_permission_allows_protected_endpoint(
    application: FastAPI, client: TestClient
) -> None:
    install_protected_endpoint(application)
    application.dependency_overrides[get_current_identity] = lambda: identity(
        PermissionCode.FORM_DESIGN
    )

    response = client.get("/test-only/protected")

    assert response.status_code == 200
    assert response.json() == {"allowed": True}


def test_role_assignment_endpoint_rejects_direct_unauthorized_request(
    application: FastAPI, client: TestClient
) -> None:
    async def database_override() -> AsyncSession:
        return cast(AsyncSession, object())

    application.dependency_overrides[get_current_identity] = lambda: identity(
        PermissionCode.ENTITY_READ
    )
    application.dependency_overrides[get_database_session] = database_override

    response = client.post(
        f"/api/v1/users/{uuid4()}/roles",
        json={"role_code": "SYSTEM_ADMIN"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
