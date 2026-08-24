"""Import upload and source inspection API schemas."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

type ImportSample = str | int | float | bool | None


class ImportColumnInspectionResponse(BaseModel):
    name: str
    sample_values: tuple[ImportSample, ...]


class ImportSheetInspectionResponse(BaseModel):
    name: str
    row_count: int
    columns: tuple[ImportColumnInspectionResponse, ...]


class ImportUploadResponse(BaseModel):
    import_job_id: UUID
    status: str
    sheets: tuple[ImportSheetInspectionResponse, ...]


class ImportProfileAssignment(BaseModel):
    import_profile_id: UUID


class ImportJobStatusResponse(BaseModel):
    import_job_id: UUID
    status: str
    import_profile_id: UUID | None


class ImportValidationErrorResponse(BaseModel):
    row_number: int | None = Field(default=None, ge=1)
    field: str
    code: str


class ImportDryRunSummaryResponse(BaseModel):
    rows_read: int
    rows_valid: int
    rows_invalid: int
    records_to_create: int
    records_to_update: int
    records_unchanged: int
    conflicts: int


class ImportDryRunResponse(BaseModel):
    import_job_id: UUID
    status: str
    summary: ImportDryRunSummaryResponse
    validation_errors: tuple[ImportValidationErrorResponse, ...]


ImportConflictResolution = Literal["MERGE", "REPLACE", "SKIP"]
ImportConflictResolutionStatus = Literal[
    "ALL", "UNRESOLVED", "RESOLVED", "MERGE", "REPLACE", "SKIP"
]


class ImportConflictResponse(BaseModel):
    id: UUID
    import_job_id: UUID
    row_number: int | None
    entity_id: UUID | None
    attribute_key: str | None
    existing_value: object | None
    imported_value: object | None
    resolution: ImportConflictResolution | None


class ImportConflictListResponse(BaseModel):
    items: tuple[ImportConflictResponse, ...]
    page: int
    page_size: int
    total: int
    unresolved: int


class ImportConflictResolutionRequest(BaseModel):
    resolution: ImportConflictResolution


class ImportBulkResolutionRequest(BaseModel):
    resolution: ImportConflictResolution
    conflict_ids: tuple[UUID, ...] = Field(min_length=1, max_length=1_000)


class ImportConflictResolutionResult(BaseModel):
    import_job_id: UUID
    status: str
    resolved: int
    unresolved: int
