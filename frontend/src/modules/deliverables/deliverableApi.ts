import { apiRequest } from '../../api/client'

export type PackageResourceKind = 'ENTITY' | 'DOCUMENT_VERSION' | 'FORM_INSTANCE'

export interface DeliverableRequirement {
  key: string
  label: string
  resource_kind: PackageResourceKind
  required: boolean
}

export interface PackageItem {
  id: string
  resource_kind: PackageResourceKind
  resource_id: string
  resource_version: number | null
  label_snapshot: string
  is_required: boolean
  metadata_snapshot: Record<string, unknown>
}

export interface PackageResourceOption {
  id: string
  resource_kind: PackageResourceKind
  label: string
  resource_version: number | null
}

export interface DeliverableVersion {
  id: string
  version_number: number
  summary: string | null
  created_by: string | null
  created_at: string
  items: PackageItem[]
}

export interface Submission {
  id: string
  deliverable_version_id: string
  sequence_number: number
  submission_kind: 'SUBMISSION' | 'RESUBMISSION'
  prior_submission_id: string | null
  submitter_id: string | null
  statement: string
  recipient_ids: string[]
  submitted_at: string
  withdrawn_at: string | null
  withdrawal_reason: string | null
}

export interface WorkflowAction {
  key: string
  label: string
  authority_kind: string
  reason_required: boolean
}

export interface WorkflowProjection {
  id: string
  current_state_key: string
  current_state_label: string
  version: number
  target_version: number | null
  available_actions: WorkflowAction[]
}

export interface Deliverable {
  id: string
  workspace_id: string
  phase_id: string
  key: string
  name: string
  description: string | null
  owner_id: string | null
  internal_reviewer_id: string | null
  contributor_ids: string[]
  internal_due_at: string | null
  official_due_at: string | null
  requirements: DeliverableRequirement[]
  readiness: { ready: boolean; total_required: number; completed_required: number; missing: string[] }
  latest_version: DeliverableVersion | null
  latest_submission: Submission | null
  workflow: WorkflowProjection | null
  created_at: string
  updated_at: string
  version: number
}

export interface DeliverableCreate {
  name: string
  description: string | null
  owner_id: string
  contributor_ids: string[]
  internal_reviewer_id: string
  internal_due_at: string | null
  official_due_at: string | null
  requirements: DeliverableRequirement[]
}

export function listDeliverables(phaseId: string): Promise<Deliverable[]> {
  return apiRequest<Deliverable[]>(`/phases/${phaseId}/deliverables`)
}

export function createDeliverable(
  phaseId: string,
  values: DeliverableCreate,
): Promise<Deliverable> {
  return apiRequest<Deliverable>(`/phases/${phaseId}/deliverables`, {
    method: 'POST', body: JSON.stringify(values),
  })
}

export function createDeliverableVersion(
  deliverableId: string,
  values: { summary: string | null; items: Array<{ resource_kind: PackageResourceKind; resource_id: string; requirement_key: string | null }> },
): Promise<Deliverable> {
  return apiRequest<Deliverable>(`/deliverables/${deliverableId}/versions`, {
    method: 'POST', body: JSON.stringify(values),
  })
}

export function searchPackageOptions(
  deliverableId: string,
  kind: PackageResourceKind,
  search: string,
): Promise<PackageResourceOption[]> {
  const query = new URLSearchParams({ kind, search, limit: '10' })
  return apiRequest<PackageResourceOption[]>(
    `/deliverables/${deliverableId}/package-options?${query.toString()}`,
  )
}

export function submitDeliverable(
  deliverableId: string,
  values: { deliverable_version_id: string; statement: string; recipient_ids: string[]; related_comment_ids: string[]; prior_submission_id: string | null; idempotency_key: string },
): Promise<Deliverable> {
  return apiRequest<Deliverable>(`/deliverables/${deliverableId}/submissions`, {
    method: 'POST', body: JSON.stringify(values),
  })
}

export function withdrawSubmission(submissionId: string, reason: string): Promise<Submission> {
  return apiRequest<Submission>(`/submissions/${submissionId}/withdrawals`, {
    method: 'POST', body: JSON.stringify({ reason, idempotency_key: crypto.randomUUID() }),
  })
}

export function transitionDeliverableReview(
  deliverableId: string,
  workflowVersion: number,
  actionKey: string,
  reason: string | null,
): Promise<Deliverable> {
  return apiRequest<Deliverable>(`/deliverables/${deliverableId}/actions/${actionKey}`, {
    method: 'POST',
    body: JSON.stringify({
      expected_version: workflowVersion,
      idempotency_key: crypto.randomUUID(),
      reason,
    }),
  })
}
