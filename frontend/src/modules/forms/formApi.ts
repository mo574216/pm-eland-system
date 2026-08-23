import { apiRequest } from '../../api/client'
import type { FormInstance, FormRenderContract, FormSummary } from './types'

interface FormList {
  items: FormSummary[]
  page: number
  page_size: number
  total: number
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

export function renderForm(formId: string, entityId: string): Promise<FormRenderContract> {
  return apiRequest<FormRenderContract>(`/forms/${formId}/render?entity_id=${entityId}`)
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
