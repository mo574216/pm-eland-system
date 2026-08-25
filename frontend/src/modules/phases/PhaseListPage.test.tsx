import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { PhaseListPage } from './PhaseListPage'
import { createPhase, listPhases, setPhaseLocked, updatePhaseStatus } from './phaseApi'

vi.mock('./phaseApi', () => ({
  createPhase: vi.fn(), listPhases: vi.fn(), setPhaseLocked: vi.fn(), updatePhaseStatus: vi.fn(),
}))

const phase = {
  id: '10000000-0000-0000-0000-000000000001', workspace_id: 'workspace-1', key: 'phase_demo',
  name: 'شناخت وضع موجود', description: 'مرحله آغازین', sequence_number: 1,
  status: 'PLANNED' as const, is_locked: false, locked_by: null, locked_at: null,
  created_at: '2026-08-25T00:00:00Z', updated_at: '2026-08-25T00:00:00Z', version: 1,
}

describe('PhaseListPage', () => {
  beforeEach(() => {
    vi.mocked(listPhases).mockResolvedValue([phase])
    vi.mocked(createPhase).mockResolvedValue(phase)
    vi.mocked(updatePhaseStatus).mockResolvedValue({ ...phase, status: 'IN_PROGRESS', version: 2 })
    vi.mocked(setPhaseLocked).mockResolvedValue({ ...phase, is_locked: true, version: 2 })
  })

  it('creates, progresses, and locks a named phase without technical keys', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={['/workspaces/workspace-1/phases']}>
        <Routes><Route path="/workspaces/:workspaceId/phases" element={<PhaseListPage />} /></Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('1. شناخت وضع موجود')).toBeVisible()
    await user.type(screen.getByRole('textbox', { name: /نام مرحله/ }), 'تحلیل')
    await user.click(screen.getByRole('button', { name: 'افزودن مرحله' }))
    expect(createPhase).toHaveBeenCalledWith('workspace-1', expect.objectContaining({ name: 'تحلیل' }))

    await user.click(screen.getByLabelText('وضعیت مرحله'))
    await user.click(screen.getByRole('option', { name: 'در حال اجرا' }))
    await user.click(screen.getByRole('button', { name: 'ذخیره وضعیت' }))
    expect(updatePhaseStatus).toHaveBeenCalledWith(phase, 'IN_PROGRESS')

    await user.click(screen.getByRole('button', { name: 'قفل مرحله' }))
    expect(setPhaseLocked).toHaveBeenCalledWith(phase.id, true)
  })
})
