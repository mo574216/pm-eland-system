import { apiRequest } from '../../api/client'
import type { ImportProfile, ImportProfileCreate, ImportProfileList, ImportUploadResult } from './types'

export function uploadImport(workspaceId: string, file: File): Promise<ImportUploadResult> {
  const body = new FormData()
  body.append('file', file)
  return apiRequest<ImportUploadResult>(`/workspaces/${workspaceId}/imports`, {
    method: 'POST',
    body,
  })
}

export function createImportProfile(
  workspaceId: string,
  payload: ImportProfileCreate,
): Promise<ImportProfile> {
  return apiRequest<ImportProfile>(`/workspaces/${workspaceId}/import-profiles`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function listImportProfiles(workspaceId: string): Promise<ImportProfileList> {
  return apiRequest<ImportProfileList>(
    `/workspaces/${workspaceId}/import-profiles?page=1&page_size=200`,
  )
}
