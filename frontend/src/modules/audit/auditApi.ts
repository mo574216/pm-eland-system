import { apiRequest } from '../../api/client'

export interface AuditEntry {
  id: string
  action: string
  resource_type: string
  resource_id: string | null
  source: string
  actor_name: string
  before_state: Record<string, unknown> | null
  after_state: Record<string, unknown> | null
  created_at: string
}

export interface AuditHistory {
  items: AuditEntry[]
  total: number
  page: number
  page_size: number
}

export function getAuditHistory(workspaceId: string, page: number): Promise<AuditHistory> {
  return apiRequest<AuditHistory>(`/workspaces/${workspaceId}/audit?page=${page}&page_size=25`)
}
