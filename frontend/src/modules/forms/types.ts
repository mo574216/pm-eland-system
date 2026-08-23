export type FormFieldType =
  | 'TEXT'
  | 'RICH_TEXT'
  | 'INTEGER'
  | 'DECIMAL'
  | 'BOOLEAN'
  | 'DATE'
  | 'DATETIME'
  | 'ENUM'
  | 'MULTI_ENUM'
  | 'USER_REFERENCE'
  | 'ENTITY_REFERENCE'
  | 'FILE_REFERENCE'
  | 'TABLE'

export interface FormOption {
  value: string
  label: string
}

export interface FormRenderField {
  key: string
  label: string
  type: FormFieldType
  required: boolean
  read_only: boolean
  visible: boolean
  value: unknown
  has_value: boolean
  value_source: 'CURRENT' | 'INHERITED' | 'DEFAULT' | 'NONE'
  configuration: Record<string, unknown>
  visibility_rule: Record<string, unknown>
  validation_rule: Record<string, unknown>
}

export interface TableColumn {
  key: string
  label: string
  type: Exclude<FormFieldType, 'TABLE'>
  required?: boolean
  configuration?: Record<string, unknown>
}
