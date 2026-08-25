import { screen } from '@testing-library/react'

import { renderWithProviders } from '../../test/render'
import { DashboardKpis } from './DashboardKpis'
import { getDashboardSummary } from './dashboardApi'

vi.mock('./dashboardApi', () => ({ getDashboardSummary: vi.fn() }))

it('renders live project KPIs and phase progress', async () => {
  vi.mocked(getDashboardSummary).mockResolvedValue({
    entity_count: 12, document_count: 4,
    phases: { total: 3, completed: 2, percent: 67 },
    deliverables: { pending: 5, completed: 7 },
  })
  renderWithProviders(<DashboardKpis workspaceId="workspace-1" />)

  expect(await screen.findByText('۱۲')).toBeVisible()
  expect(screen.getByText('۴')).toBeVisible()
  expect(screen.getByText('۵')).toBeVisible()
  expect(screen.getByText('۶۷٪')).toBeVisible()
  expect(screen.getByText('۲ مرحله از ۳ مرحله تکمیل شده است.')).toBeVisible()
  expect(getDashboardSummary).toHaveBeenCalledWith('workspace-1')
})
