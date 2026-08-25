"""Server-defined workspace KPI schemas."""

from pydantic import BaseModel, Field


class PhaseProgress(BaseModel):
    total: int = Field(ge=0)
    completed: int = Field(ge=0)
    percent: int = Field(ge=0, le=100)


class DeliverableProgress(BaseModel):
    pending: int = Field(ge=0)
    completed: int = Field(ge=0)


class DashboardSummaryResponse(BaseModel):
    entity_count: int = Field(ge=0)
    document_count: int = Field(ge=0)
    phases: PhaseProgress
    deliverables: DeliverableProgress
