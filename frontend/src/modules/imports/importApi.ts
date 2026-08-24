import { apiRequest } from '../../api/client'
import type { ImportUploadResult } from './types'

export function uploadImport(workspaceId: string, file: File): Promise<ImportUploadResult> {
  const body = new FormData()
  body.append('file', file)
  return apiRequest<ImportUploadResult>(`/workspaces/${workspaceId}/imports`, {
    method: 'POST',
    body,
  })
}
