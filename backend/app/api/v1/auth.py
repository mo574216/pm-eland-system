"""Authentication endpoints for bearer access and rotating refresh sessions."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import get_auth_service, get_current_identity
from app.api.envelopes import success_envelope
from app.core.config import Settings
from app.core.database import get_database_session
from app.core.exceptions import AuthenticationRequiredError
from app.schemas.auth import (
    CurrentUserResponse,
    CurrentUserWorkspace,
    LoginRequest,
    TokenResponse,
    UserSummary,
)
from app.services.auth import AuthenticatedIdentity, AuthService, IssuedTokens
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.refresh_idle_expiry_seconds,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite="strict",
        path="/",
    )


def _token_response(tokens: IssuedTokens, settings: Settings) -> dict[str, object]:
    data = TokenResponse(
        access_token=tokens.access_token,
        expires_in=settings.jwt_expiry_seconds,
        user=UserSummary(
            id=tokens.identity.user.id,
            username=tokens.identity.user.username,
            display_name=tokens.identity.user.display_name,
            roles=tokens.identity.roles,
        ),
    )
    return success_envelope(data.model_dump(mode="json"))


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, object]:
    tokens = await service.login(payload.username, payload.password)
    _set_refresh_cookie(response, tokens.refresh_token, request.app.state.settings)
    return _token_response(tokens, request.app.state.settings)


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, object]:
    allowed_origins = {
        str(origin).rstrip("/") for origin in request.app.state.settings.cors_origins
    }
    refresh_token = request.cookies.get(request.app.state.settings.auth_cookie_name)
    if request.headers.get("origin") not in allowed_origins or refresh_token is None:
        raise AuthenticationRequiredError
    tokens = await service.refresh(refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token, request.app.state.settings)
    return _token_response(tokens, request.app.state.settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    _: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    refresh_token = request.cookies.get(request.app.state.settings.auth_cookie_name)
    await service.logout(refresh_token)
    response.delete_cookie(
        key=request.app.state.settings.auth_cookie_name,
        secure=request.app.state.settings.auth_cookie_secure,
        httponly=True,
        samesite="strict",
        path="/",
    )


@router.get("/me")
async def me(
    identity: Annotated[AuthenticatedIdentity, Depends(get_current_identity)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> dict[str, object]:
    workspaces, _ = await WorkspaceService(session, identity).list_workspaces(
        page=1,
        page_size=200,
        status=None,
        search=None,
    )
    data = CurrentUserResponse(
        id=identity.user.id,
        username=identity.user.username,
        display_name=identity.user.display_name,
        roles=identity.roles,
        permissions=identity.permissions,
        workspaces=tuple(
            CurrentUserWorkspace(id=workspace.id, name=workspace.name) for workspace in workspaces
        ),
    )
    return success_envelope(data.model_dump(mode="json"))
