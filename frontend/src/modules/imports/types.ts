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
