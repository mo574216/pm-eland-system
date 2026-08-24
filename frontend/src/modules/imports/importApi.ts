import { apiRequest } from '../../api/client'
import type {
  ImportDryRunResult,
  ImportConflictList,
  ImportConflictResolution,
  ImportJobStatus,
  ImportProfile,
  ImportProfileCreate,
  ImportProfileList,
  ImportUploadResult,
  ImportResolutionResult,
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

export function listImportConflicts(
  importJobId: string,
  page: number,
  pageSize: number,
): Promise<ImportConflictList> {
  return apiRequest<ImportConflictList>(
    `/imports/${importJobId}/conflicts?page=${String(page)}&page_size=${String(pageSize)}&resolution_status=ALL`,
  )
}

export function resolveImportConflict(
  importJobId: string,
  conflictId: string,
  resolution: ImportConflictResolution,
): Promise<ImportResolutionResult> {
  return apiRequest<ImportResolutionResult>(`/imports/${importJobId}/conflicts/${conflictId}`, {
    method: 'PUT',
    body: JSON.stringify({ resolution }),
  })
}

export function resolveImportConflictsBulk(
  importJobId: string,
  conflictIds: string[],
  resolution: ImportConflictResolution,
): Promise<ImportResolutionResult> {
  return apiRequest<ImportResolutionResult>(`/imports/${importJobId}/resolve-bulk`, {
    method: 'POST',
    body: JSON.stringify({ conflict_ids: conflictIds, resolution }),
  })
}
