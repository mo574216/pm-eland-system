import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { WorkspaceDashboardPage } from './WorkspaceDashboardPage'

const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'

function LocationProbe() {
  return <span data-testid="location">{useLocation().pathname}</span>
}

describe('WorkspaceDashboardPage', () => {
  it('separates working capability actions from planned modules', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${workspaceId}`]}>
        <Routes>
          <Route path="/workspaces/:workspaceId" element={<WorkspaceDashboardPage />} />
          <Route path="*" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'نمای یکپارچه فضای کاری شما' })).toBeVisible()
    expect(screen.getAllByRole('button', { name: 'ورود به بخش' })).toHaveLength(5)
    expect(screen.getByRole('heading', { name: 'فرم‌های پویا' })).toBeVisible()
    expect(screen.getAllByText('در برنامه توسعه')).toHaveLength(2)
    expect(screen.getByText('اعلان جدیدی برای نمایش وجود ندارد.')).toBeVisible()

    await user.click(screen.getAllByRole('button', { name: 'ورود به بخش' })[0])
    expect(screen.getByTestId('location')).toHaveTextContent(`/workspaces/${workspaceId}/entities`)
  })
})
