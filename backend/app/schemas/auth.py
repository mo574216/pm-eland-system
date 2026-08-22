"""Authentication request and response schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    display_name: str | None
    roles: tuple[str, ...]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth token type, not a credential
    expires_in: int
    user: UserSummary


class CurrentUserWorkspace(BaseModel):
    id: UUID
    name: str


class CurrentUserResponse(UserSummary):
    permissions: tuple[str, ...]
    workspaces: tuple[CurrentUserWorkspace, ...] = ()
