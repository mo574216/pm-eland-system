import { apiRequest } from '../../api/client'
import type {
  FormDefinition,
  FormFieldType,
  FormInstance,
  FormRenderContract,
  FormSectionDefinition,
  FormSummary,
} from './types'

export interface FormList {
  items: FormSummary[]
  page: number
  page_size: number
  total: number
}

export function listForms(workspaceId: string): Promise<FormList> {
  return apiRequest<FormList>(`/workspaces/${workspaceId}/forms?page=1&page_size=200`)
}

export function createForm(
  workspaceId: string,
  values: { key?: string; name: string; description: string | null; entity_type_id: string },
): Promise<FormDefinition> {
  return apiRequest<FormDefinition>(`/workspaces/${workspaceId}/forms`, {
    method: 'POST',
    body: JSON.stringify(values),
  })
}

export function getForm(formId: string): Promise<FormDefinition> {
  return apiRequest<FormDefinition>(`/forms/${formId}`)
}

export function updateFormSections(
  formId: string,
  sections: FormSectionDefinition[],
): Promise<FormDefinition> {
  return apiRequest<FormDefinition>(`/forms/${formId}`, {
    method: 'PATCH',
    body: JSON.stringify({ schema_json: { sections } }),
  })
}

export function addFormField(
  formId: string,
  values: {
    key: string
    label: string
    field_type: FormFieldType
    attribute_definition_id: string | null
    section_key: string | null
    display_order: number
    is_required: boolean
    is_read_only: boolean
    configuration: Record<string, unknown>
    visibility_rule: Record<string, unknown>
    validation_rule: Record<string, unknown>
    inheritance_rule: Record<string, unknown>
  },
): Promise<FormDefinition['fields'][number]> {
  return apiRequest<FormDefinition['fields'][number]>(`/forms/${formId}/fields`, {
    method: 'POST',
    body: JSON.stringify(values),
  })
}

export function publishForm(formId: string): Promise<FormDefinition> {
  return apiRequest<FormDefinition>(`/forms/${formId}/publish`, { method: 'POST' })
}

export function createNewFormVersion(formId: string): Promise<FormDefinition> {
  return apiRequest<FormDefinition>(`/forms/${formId}/new-version`, { method: 'POST' })
}

export function listPublishedForms(workspaceId: string, entityTypeId: string): Promise<FormList> {
  const query = new URLSearchParams({
    entity_type_id: entityTypeId,
    status: 'PUBLISHED',
    page: '1',
    page_size: '200',
  })
  return apiRequest<FormList>(`/workspaces/${workspaceId}/forms?${query.toString()}`)
}

export function renderForm(formId: string, entityId?: string): Promise<FormRenderContract> {
  const query = entityId ? `?entity_id=${entityId}` : ''
  return apiRequest<FormRenderContract>(`/forms/${formId}/render${query}`)
}

export function createFormInstance(formId: string, entityId: string): Promise<FormInstance> {
  return apiRequest<FormInstance>(`/forms/${formId}/instances`, {
    method: 'POST',
    body: JSON.stringify({ entity_id: entityId }),
  })
}

export function saveFormInstance(
  instanceId: string,
  values: Record<string, unknown>,
  version: number,
): Promise<FormInstance> {
  return apiRequest<FormInstance>(`/form-instances/${instanceId}`, {
    method: 'PATCH',
    body: JSON.stringify({ values, version }),
  })
}
