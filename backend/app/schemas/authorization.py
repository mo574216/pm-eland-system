"""Role assignment API schemas."""

from pydantic import BaseModel, Field


class RoleAssignmentRequest(BaseModel):
    role_code: str = Field(min_length=1, max_length=100, pattern=r"^[A-Z][A-Z0-9_]*$")


class RoleAssignmentResponse(BaseModel):
    role_code: str
    changed: bool
