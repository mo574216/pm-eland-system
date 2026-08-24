import { apiRequest } from '../../api/client'
import type {
  ImportDryRunResult,
  ImportJobStatus,
  ImportProfile,
  ImportProfileCreate,
  ImportProfileList,
  ImportUploadResult,
} from './types'

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

export function assignImportProfile(
  importJobId: string,
  importProfileId: string,
): Promise<ImportJobStatus> {
  return apiRequest<ImportJobStatus>(`/imports/${importJobId}/mapping`, {
    method: 'PUT',
    body: JSON.stringify({ import_profile_id: importProfileId }),
  })
}

export function dryRunImport(importJobId: string): Promise<ImportDryRunResult> {
  return apiRequest<ImportDryRunResult>(`/imports/${importJobId}/dry-run`, {
    method: 'POST',
  })
}
