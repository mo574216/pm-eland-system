import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { listWorkspaceMembers } from '../workspaces/workspaceApi'
import { DeliverablesPanel } from './DeliverablesPanel'
import {
  createDeliverable,
  createDeliverableVersion,
  recordSubmissionReviewOutcome,
  listDeliverables,
  searchPackageOptions,
  addSubmissionReviewComment,
  submitDeliverable,
  transitionDeliverableReview,
  withdrawSubmission,
} from './deliverableApi'

vi.mock('../workspaces/workspaceApi', () => ({ listWorkspaceMembers: vi.fn() }))
vi.mock('./deliverableApi', () => ({
  createDeliverable: vi.fn(), createDeliverableVersion: vi.fn(), listDeliverables: vi.fn(),
  searchPackageOptions: vi.fn(), submitDeliverable: vi.fn(), withdrawSubmission: vi.fn(),
  transitionDeliverableReview: vi.fn(),
  recordSubmissionReviewOutcome: vi.fn(), addSubmissionReviewComment: vi.fn(),
}))

const member = {
  id: 'membership-1', user_id: '10000000-0000-0000-0000-000000000001', username: 'leader',
  display_name: 'رهبر پروژه', role_id: 'role-1', role_code: 'CONTRACTOR_PROJECT_LEADER',
  status: 'ACTIVE' as const, created_at: '2026-08-25T00:00:00Z',
}
const deliverable = {
  id: '20000000-0000-0000-0000-000000000001', workspace_id: 'workspace-1', phase_id: 'phase-1',
  key: 'deliverable_generated', name: 'بسته مشخصات', description: 'خروجی رسمی مرحله',
  owner_id: member.user_id, internal_reviewer_id: null, contributor_ids: [],
  internal_due_at: null, official_due_at: null, requirements: [],
  readiness: { ready: false, total_required: 0, completed_required: 0, missing: [] },
  latest_version: null, latest_submission: null, workflow: null, created_at: '2026-08-25T00:00:00Z',
  updated_at: '2026-08-25T00:00:00Z', version: 1,
}

describe('DeliverablesPanel', () => {
  beforeEach(() => {
    vi.mocked(listWorkspaceMembers).mockResolvedValue([member])
    vi.mocked(listDeliverables).mockResolvedValue([deliverable])
    vi.mocked(createDeliverable).mockResolvedValue(deliverable)
    vi.mocked(createDeliverableVersion).mockResolvedValue(deliverable)
    vi.mocked(searchPackageOptions).mockResolvedValue([])
    vi.mocked(submitDeliverable).mockResolvedValue(deliverable)
    vi.mocked(transitionDeliverableReview).mockResolvedValue(deliverable)
    vi.mocked(withdrawSubmission).mockRejectedValue(new Error('unused'))
    vi.mocked(recordSubmissionReviewOutcome).mockRejectedValue(new Error('unused'))
    vi.mocked(addSubmissionReviewComment).mockRejectedValue(new Error('unused'))
  })

  it('creates a named deliverable inside its phase with human-readable people selection', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DeliverablesPanel locked={false} phaseId="phase-1" workspaceId="workspace-1" />)

    expect(await screen.findByText('بسته مشخصات')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'افزودن تحویل‌دادنی' }))
    await user.type(screen.getByRole('textbox', { name: 'نام تحویل‌دادنی' }), 'گزارش مرحله')
    await user.click(screen.getByRole('combobox', { name: /مسئول تحویل‌دادنی/ }))
    await user.click(screen.getByRole('option', { name: 'رهبر پروژه' }))
    await user.click(screen.getByRole('combobox', { name: 'بازبین داخلی' }))
    await user.click(screen.getByRole('option', { name: 'رهبر پروژه' }))
    await user.click(screen.getByRole('button', { name: 'ایجاد تحویل‌دادنی' }))

    expect(createDeliverable).toHaveBeenCalledWith('phase-1', expect.objectContaining({
      name: 'گزارش مرحله', owner_id: member.user_id,
    }))
    expect(screen.queryByText('deliverable_generated')).not.toBeInTheDocument()
  })

  it('renders and executes only the backend-returned review action', async () => {
    const user = userEvent.setup()
    vi.mocked(listDeliverables).mockResolvedValue([{
      ...deliverable,
      readiness: { ready: true, total_required: 0, completed_required: 0, missing: [] },
      workflow: {
        id: 'workflow-1', current_state_key: 'preparation', current_state_label: 'در حال آماده‌سازی',
        version: 1, target_version: 1,
        available_actions: [{ key: 'request_internal_review', label: 'ارسال برای بازبینی داخلی', authority_kind: 'CONTRIBUTION', reason_required: false }],
      },
    }])
    renderWithProviders(<DeliverablesPanel locked={false} phaseId="phase-1" workspaceId="workspace-1" />)

    await user.click(await screen.findByRole('button', { name: 'ارسال برای بازبینی داخلی' }))
    expect(transitionDeliverableReview).toHaveBeenCalledWith(
      deliverable.id, 1, 'request_internal_review', null,
    )
    expect(screen.queryByRole('button', { name: 'تأیید آمادگی برای ارسال' })).not.toBeInTheDocument()
  })

  it('offers only backend-returned version-bound external review outcomes', async () => {
    const user = userEvent.setup()
    vi.mocked(recordSubmissionReviewOutcome).mockResolvedValue({} as never)
    vi.mocked(listDeliverables).mockResolvedValue([{
      ...deliverable,
      latest_version: {
        id: 'version-1', version_number: 1, summary: null, created_by: member.user_id,
        created_at: '2026-08-25T00:00:00Z', items: [],
      },
      latest_submission: {
        id: 'submission-1', deliverable_version_id: 'version-1', sequence_number: 1,
        submission_kind: 'SUBMISSION', prior_submission_id: null, submitter_id: member.user_id,
        statement: 'ارسال رسمی', recipient_ids: [member.user_id], submitted_at: '2026-08-25T00:00:00Z',
        withdrawn_at: null, withdrawal_reason: null, review_comments: [], review_outcomes: [],
        available_review_actions: [{ outcome_kind: 'REVISION_REQUEST', authority_kind: 'PROJECT_REVIEW', label: 'درخواست اصلاح پروژه', changes_workflow: true }],
      },
      workflow: {
        id: 'workflow-1', current_state_key: 'submitted', current_state_label: 'ارسال‌شده',
        version: 4, target_version: 1, available_actions: [],
      },
    }])
    renderWithProviders(<DeliverablesPanel locked={false} phaseId="phase-1" workspaceId="workspace-1" />)

    await user.click(await screen.findByRole('button', { name: 'بازبینی رسمی' }))
    await user.click(screen.getByRole('combobox', { name: 'نتیجه و مرجع اختیار' }))
    await user.click(screen.getByRole('option', { name: 'درخواست اصلاح پروژه' }))
    await user.type(screen.getByRole('textbox', { name: 'شرح نتیجه بازبینی' }), 'نسخه اصلاح شود')
    await user.click(screen.getByRole('button', { name: 'ثبت نتیجه بازبینی' }))

    expect(recordSubmissionReviewOutcome).toHaveBeenCalledWith('submission-1', expect.objectContaining({
      outcome_kind: 'REVISION_REQUEST', authority_kind: 'PROJECT_REVIEW',
      expected_workflow_version: 4,
    }))
  })
})
