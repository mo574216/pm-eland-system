"""Import upload and source inspection API schemas."""

from uuid import UUID

from pydantic import BaseModel

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
