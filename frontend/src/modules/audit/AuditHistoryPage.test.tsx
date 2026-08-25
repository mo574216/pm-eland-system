import { screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { AuditHistoryPage } from './AuditHistoryPage'
import { getAuditHistory } from './auditApi'

vi.mock('./auditApi', () => ({ getAuditHistory: vi.fn() }))

it('shows a friendly workspace change history', async () => {
  vi.mocked(getAuditHistory).mockResolvedValue({
    items: [{
      id: 'audit-1', action: 'ENTITY_UPDATED', resource_type: 'entity', resource_id: 'entity-1',
      source: 'API', actor_name: 'اکبر مصطفوی', before_state: null, after_state: null,
      created_at: '2026-08-25T08:30:00Z',
    }],
    total: 1, page: 1, page_size: 25,
  })
  renderWithProviders(
    <MemoryRouter initialEntries={['/workspaces/workspace-1/audit']}>
      <Routes>
        <Route path="/workspaces/:workspaceId/audit" element={<AuditHistoryPage />} />
      </Routes>
    </MemoryRouter>,
  )

  expect(await screen.findByText('ویرایش شد')).toBeVisible()
  expect(screen.getByText('اکبر مصطفوی')).toBeVisible()
  expect(getAuditHistory).toHaveBeenCalledWith('workspace-1', 1)
})
