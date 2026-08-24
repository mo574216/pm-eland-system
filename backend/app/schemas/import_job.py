"""Import upload and source inspection API schemas."""

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
