"""Read-only audit history response contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    id: UUID
    action: str
    resource_type: str
    resource_id: UUID | None
    source: str
    actor_name: str
    before_state: dict[str, object] | None
    after_state: dict[str, object] | None
    created_at: datetime


class AuditHistoryResponse(BaseModel):
    items: list[AuditEntryResponse]
    total: int
    page: int
    page_size: int
