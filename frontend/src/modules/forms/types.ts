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

export interface FormRenderSection {
  key: string | null
  label: string | null
  order: number
  configuration: Record<string, unknown>
  fields: FormRenderField[]
}

export interface FormRenderContract {
  form: {
    id: string
    key: string
    name: string
    version_number: number
    lifecycle_status: 'DRAFT' | 'PUBLISHED' | 'RETIRED'
  }
  entity_id: string | null
  sections: FormRenderSection[]
}

export interface FormSummary {
  id: string
  workspace_id: string
  entity_type_id: string | null
  key: string
  name: string
  description: string | null
  version_number: number
  lifecycle_status: 'DRAFT' | 'PUBLISHED' | 'RETIRED'
}

export interface FormSectionDefinition {
  key: string
  label: string
  display_order: number
  configuration: Record<string, unknown>
}

export interface FormDefinition extends FormSummary {
  schema_json: { sections: FormSectionDefinition[] }
  fields: Array<{
    id: string
    form_definition_id: string
    attribute_definition_id: string | null
    key: string
    label: string
    field_type: FormFieldType
    section_key: string | null
    display_order: number
    is_required: boolean
    is_read_only: boolean
    configuration: Record<string, unknown>
    visibility_rule: Record<string, unknown>
    validation_rule: Record<string, unknown>
    inheritance_rule: Record<string, unknown>
  }>
}

export interface FormInstance {
  id: string
  workspace_id: string
  form_definition_id: string
  entity_id: string
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REVISION_REQUESTED'
  values: Record<string, unknown>
  version: number
  created_at: string
  updated_at: string
  submitted_by: string | null
  submitted_at: string | null
  form: FormRenderContract['form']
}

export interface TableColumn {
  key: string
  label: string
  type: Exclude<FormFieldType, 'TABLE'>
  required?: boolean
  configuration?: Record<string, unknown>
}
