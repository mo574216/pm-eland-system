import { apiRequest } from '../../api/client'
import type { PackageResourceKind, PackageResourceOption } from '../deliverables/deliverableApi'

export interface AcceptanceCondition {
  id: string
  description: string
  responsible_id: string | null
  verifier_id: string | null
  due_at: string
  evidence_requirement: string
  mandatory: boolean
  status: string
  version: number
  available_actions: Array<'SUBMIT_EVIDENCE' | 'VERIFY' | 'REJECT_EVIDENCE'>
}

export interface AcceptanceDecision {
  id: string
  decision_kind: 'ACCEPT' | 'CONDITIONAL_ACCEPT' | 'REJECT'
  actor_id: string | null
  authority_kind: 'EMPLOYER_ACCEPTANCE'
  statement: string
  decided_at: string
  conditions: AcceptanceCondition[]
  closed_at: string | null
  closure_statement: string | null
  can_close: boolean
}

export interface AcceptancePackage {
  id: string
  workspace_id: string
  phase_id: string
  sequence_number: number
  statement: string
  employer_recipient_id: string | null
  requested_by: string | null
  created_at: string
  items: Array<{ id: string; submission_id: string; deliverable_version_id: string; review_outcome_ids: string[]; label_snapshot: string }>
  decision: AcceptanceDecision | null
  available_decisions: Array<'ACCEPT' | 'CONDITIONAL_ACCEPT' | 'REJECT'>
}

export interface AcceptanceWorkspace { can_prepare: boolean; packages: AcceptancePackage[] }

export interface AcceptanceRecipientOption {
  user_id: string
  username: string
  display_name: string | null
  role_code: string | null
}

export function getAcceptanceWorkspace(phaseId: string): Promise<AcceptanceWorkspace> {
  return apiRequest<AcceptanceWorkspace>(`/phases/${phaseId}/acceptance-workspace`)
}

export function listAcceptanceRecipientOptions(phaseId: string): Promise<AcceptanceRecipientOption[]> {
  return apiRequest<AcceptanceRecipientOption[]>(`/phases/${phaseId}/acceptance-recipient-options`)
}

export function createAcceptancePackage(
  phaseId: string, employerRecipientId: string, statement: string,
): Promise<AcceptancePackage> {
  return apiRequest<AcceptancePackage>(`/phases/${phaseId}/acceptance-packages`, {
    method: 'POST',
    body: JSON.stringify({ employer_recipient_id: employerRecipientId, statement, idempotency_key: crypto.randomUUID() }),
  })
}

export function decideAcceptancePackage(
  packageId: string,
  values: { decision_kind: string; statement: string; conditions: Array<{ description: string; responsible_id: string; verifier_id: string; due_at: string; evidence_requirement: string; mandatory: boolean }> },
): Promise<AcceptancePackage> {
  return apiRequest<AcceptancePackage>(`/acceptance-packages/${packageId}/decisions`, {
    method: 'POST', body: JSON.stringify({ ...values, idempotency_key: crypto.randomUUID() }),
  })
}

export function searchConditionEvidence(
  conditionId: string, kind: PackageResourceKind, search: string,
): Promise<PackageResourceOption[]> {
  const query = new URLSearchParams({ kind, search, limit: '10' })
  return apiRequest<PackageResourceOption[]>(`/acceptance-conditions/${conditionId}/evidence-options?${query}`)
}

export function submitConditionEvidence(
  condition: AcceptanceCondition, statement: string, resource: PackageResourceOption,
): Promise<AcceptanceCondition> {
  return apiRequest<AcceptanceCondition>(`/acceptance-conditions/${condition.id}/evidence`, {
    method: 'POST',
    body: JSON.stringify({
      expected_version: condition.version, statement,
      evidence: [{ resource_kind: resource.resource_kind, resource_id: resource.id }],
      idempotency_key: crypto.randomUUID(),
    }),
  })
}

export function verifyCondition(
  condition: AcceptanceCondition, decision: 'VERIFY' | 'REJECT_EVIDENCE', statement: string,
): Promise<AcceptanceCondition> {
  return apiRequest<AcceptanceCondition>(`/acceptance-conditions/${condition.id}/verification`, {
    method: 'POST',
    body: JSON.stringify({ expected_version: condition.version, decision, statement, idempotency_key: crypto.randomUUID() }),
  })
}

export function closeConditionalAcceptance(
  decisionId: string, statement: string,
): Promise<AcceptancePackage> {
  return apiRequest<AcceptancePackage>(`/acceptance-decisions/${decisionId}/closure`, {
    method: 'POST', body: JSON.stringify({ statement, idempotency_key: crypto.randomUUID() }),
  })
}
