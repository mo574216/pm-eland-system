import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { listWorkspaceMembers } from '../workspaces/workspaceApi'
import { AcceptancePanel } from './AcceptancePanel'
import { createAcceptancePackage, getAcceptanceWorkspace, listAcceptanceRecipientOptions } from './acceptanceApi'

vi.mock('../workspaces/workspaceApi', () => ({ listWorkspaceMembers: vi.fn() }))
vi.mock('./acceptanceApi', () => ({
  closeConditionalAcceptance: vi.fn(), createAcceptancePackage: vi.fn(),
  decideAcceptancePackage: vi.fn(), getAcceptanceWorkspace: vi.fn(),
  listAcceptanceRecipientOptions: vi.fn(),
  searchConditionEvidence: vi.fn(), submitConditionEvidence: vi.fn(), verifyCondition: vi.fn(),
}))

const member = {
  id: 'member-1', user_id: '10000000-0000-0000-0000-000000000001', username: 'employer',
  display_name: 'نماینده کارفرما', role_id: 'role-1', role_code: 'EMPLOYER_REPRESENTATIVE',
  status: 'ACTIVE' as const, created_at: '2026-08-27T00:00:00Z',
}

describe('AcceptancePanel', () => {
  beforeEach(() => {
    vi.mocked(listWorkspaceMembers).mockResolvedValue([member])
    vi.mocked(listAcceptanceRecipientOptions).mockResolvedValue([{
      user_id: member.user_id, username: member.username, display_name: member.display_name,
      role_code: member.role_code,
    }])
    vi.mocked(createAcceptancePackage).mockResolvedValue({} as never)
  })

  it('hides package creation when the backend does not authorize it', async () => {
    vi.mocked(getAcceptanceWorkspace).mockResolvedValue({ can_prepare: false, packages: [] })
    renderWithProviders(<AcceptancePanel phaseId="phase-1" workspaceId="workspace-1" />)

    await screen.findByText('پذیرش مرحله')
    expect(screen.queryByRole('button', { name: 'آماده‌سازی بسته پذیرش' })).not.toBeInTheDocument()
  })

  it('creates a phase acceptance package with a named employer selector', async () => {
    const user = userEvent.setup()
    vi.mocked(getAcceptanceWorkspace).mockResolvedValue({ can_prepare: true, packages: [] })
    renderWithProviders(<AcceptancePanel phaseId="phase-1" workspaceId="workspace-1" />)

    await user.click(await screen.findByRole('button', { name: 'آماده‌سازی بسته پذیرش' }))
    await user.click(screen.getByRole('combobox', { name: 'نماینده کارفرما برای تصمیم' }))
    await user.click(screen.getByRole('option', { name: 'نماینده کارفرما' }))
    await user.type(screen.getByRole('textbox', { name: 'شرح درخواست پذیرش' }), 'درخواست پذیرش مرحله')
    await user.click(screen.getByRole('button', { name: 'ثبت درخواست پذیرش مرحله' }))

    expect(createAcceptancePackage).toHaveBeenCalledWith(
      'phase-1', member.user_id, 'درخواست پذیرش مرحله',
    )
  })
})
