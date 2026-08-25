import { apiRequest } from '../../api/client'

export interface DashboardSummary {
  entity_count: number
  document_count: number
  phases: { total: number; completed: number; percent: number }
  deliverables: { pending: number; completed: number }
}

export function getDashboardSummary(workspaceId: string): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>(`/workspaces/${workspaceId}/dashboard-summary`)
}
