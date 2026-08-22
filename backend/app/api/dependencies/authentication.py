"""Reusable authentication dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import get_database_session
from app.core.exceptions import AuthenticationExpiredError, AuthenticationRequiredError
from app.core.security import AccessTokenExpiredError, InvalidAccessTokenError, decode_access_token
from app.services.auth import AuthenticatedIdentity, AuthService

bearer = HTTPBearer(auto_error=False)


def get_auth_service(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> AuthService:
    return AuthService(session, request.app.state.settings)


async def get_current_identity(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedIdentity:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationRequiredError
    settings: Settings = request.app.state.settings
    try:
        user_id = decode_access_token(credentials.credentials, settings)
    except AccessTokenExpiredError as exc:
        raise AuthenticationExpiredError from exc
    except InvalidAccessTokenError as exc:
        raise AuthenticationRequiredError from exc
    return await service.identity(user_id)
