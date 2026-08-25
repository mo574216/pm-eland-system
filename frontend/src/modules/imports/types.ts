export interface ImportColumnInspection {
  name: string
  sample_values: Array<string | number | boolean | null>
}

export interface ImportSheetInspection {
  name: string
  row_count: number
  columns: ImportColumnInspection[]
}

export interface ImportUploadResult {
  import_job_id: string
  status: string
  sheets: ImportSheetInspection[]
}

export type ImportTarget =
  | { target_attribute_definition_id: string; target_system_field?: never }
  | { target_attribute_definition_id?: never; target_system_field: 'name' | 'description' | 'parent_id' }

export type ImportMappingCreate = ImportTarget & {
  source_sheet: string | null
  source_column: string
  transformation_config: Record<string, unknown>
  display_order: number
}

export type MatchKey = {
  source_sheet: string | null
  source_column: string
} & (
  | { attribute_definition_id: string; system_field?: never }
  | { attribute_definition_id?: never; system_field: 'name' }
)

export type MatchingStrategy =
  | { type: 'ENTITY_ID'; source_sheet: string | null; source_column: string }
  | { type: 'UNIQUE_ATTRIBUTE'; key: MatchKey }
  | { type: 'COMPOSITE_KEY'; keys: MatchKey[] }
  | { type: 'PARENT_AND_KEY'; parent_source_sheet: string | null; parent_source_column: string; key: MatchKey }

export interface ImportProfileCreate {
  entity_type_id: string
  name: string
  description: string | null
  source_type: 'CSV' | 'XLSX'
  matching_strategy: MatchingStrategy
  configuration: Record<string, unknown>
  mappings: ImportMappingCreate[]
}

export interface ImportProfile {
  id: string
  name: string
  entity_type_id: string
  source_type: 'CSV' | 'XLSX'
  matching_strategy: MatchingStrategy
  mappings: ImportMappingCreate[]
}

export interface ImportProfileList {
  items: ImportProfile[]
  page: number
  page_size: number
  total: number
}

export interface ImportJobStatus {
  import_job_id: string
  status: string
  import_profile_id: string | null
}

export interface ImportValidationError {
  row_number: number | null
  field: string
  code: string
}

export interface ImportDryRunSummary {
  rows_read: number
  rows_valid: number
  rows_invalid: number
  records_to_create: number
  records_to_update: number
  records_unchanged: number
  conflicts: number
}

export interface ImportDryRunResult {
  import_job_id: string
  status: 'READY_FOR_REVIEW' | 'READY_TO_COMMIT' | 'VALIDATION_FAILED'
  summary: ImportDryRunSummary
  validation_errors: ImportValidationError[]
}

export type ImportConflictResolution = 'MERGE' | 'REPLACE' | 'SKIP'

export interface ImportConflict {
  id: string
  import_job_id: string
  row_number: number | null
  entity_id: string | null
  attribute_key: string | null
  existing_value: unknown
  imported_value: unknown
  resolution: ImportConflictResolution | null
}

export interface ImportConflictList {
  items: ImportConflict[]
  page: number
  page_size: number
  total: number
  unresolved: number
}

export interface ImportResolutionResult {
  import_job_id: string
  status: string
  resolved: number
  unresolved: number
}

export interface ImportCommitSummary {
  rows_read: number
  records_created: number
  records_updated: number
  records_unchanged: number
  records_skipped: number
  conflicts_resolved: number
  invalid_rows: number
}

export interface ImportCommitResult {
  import_job_id: string
  status: string
  summary: ImportCommitSummary
}
