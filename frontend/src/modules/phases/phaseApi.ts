import { apiRequest } from '../../api/client'

export type PhaseStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'ARCHIVED'

export interface Phase {
  id: string
  workspace_id: string
  key: string
  name: string
  description: string | null
  sequence_number: number
  status: PhaseStatus
  is_locked: boolean
  locked_by: string | null
  locked_at: string | null
  created_at: string
  updated_at: string
  version: number
}

export function listPhases(workspaceId: string): Promise<Phase[]> {
  return apiRequest<Phase[]>(`/workspaces/${workspaceId}/phases`)
}

export function createPhase(
  workspaceId: string,
  values: { name: string; description: string | null; sequence_number: number },
): Promise<Phase> {
  return apiRequest<Phase>(`/workspaces/${workspaceId}/phases`, {
    method: 'POST', body: JSON.stringify(values),
  })
}

export function updatePhaseStatus(phase: Phase, status: PhaseStatus): Promise<Phase> {
  return apiRequest<Phase>(`/phases/${phase.id}`, {
    method: 'PATCH', body: JSON.stringify({ status, version: phase.version }),
  })
}

export function setPhaseLocked(phaseId: string, locked: boolean): Promise<Phase> {
  return apiRequest<Phase>(`/phases/${phaseId}/${locked ? 'lock' : 'unlock'}`, { method: 'POST' })
}
