import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { WorkspaceListPage } from './WorkspaceListPage'
import { listWorkspaces } from './workspaceApi'

vi.mock('./workspaceApi', () => ({ listWorkspaces: vi.fn() }))

function LocationProbe() {
  return <span>{useLocation().pathname}</span>
}

describe('WorkspaceListPage', () => {
  beforeEach(() => {
    vi.mocked(listWorkspaces).mockReset()
  })

  it('shows only the accessible workspaces returned by the API', async () => {
    vi.mocked(listWorkspaces).mockResolvedValue({
      items: [
        {
          id: '6ab93847-d2b3-43b8-aae1-15662031feb8',
          name: 'معماری سازمانی',
          slug: 'enterprise-architecture',
          description: 'فضای کاری قابل دسترس',
          owner_id: null,
          status: 'ACTIVE',
          configuration: {},
          created_at: '2026-08-22T00:00:00Z',
          updated_at: '2026-08-22T00:00:00Z',
          archived_at: null,
          version: 1,
        },
      ],
      page: 1,
      page_size: 200,
      total: 1,
    })

    renderWithProviders(
      <MemoryRouter>
        <WorkspaceListPage />
        <LocationProbe />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'معماری سازمانی' })).toBeInTheDocument()
    expect(screen.getByText('فضای کاری قابل دسترس')).toBeInTheDocument()
    expect(screen.queryByText('فضای کاری غیرمجاز')).not.toBeInTheDocument()
  })

  it('selects a workspace when it is opened', async () => {
    vi.mocked(listWorkspaces).mockResolvedValue({
      items: [
        {
          id: '6ab93847-d2b3-43b8-aae1-15662031feb8',
          name: 'معماری سازمانی',
          slug: 'enterprise-architecture',
          description: null,
          owner_id: null,
          status: 'ACTIVE',
          configuration: {},
          created_at: '2026-08-22T00:00:00Z',
          updated_at: '2026-08-22T00:00:00Z',
          archived_at: null,
          version: 1,
        },
      ],
      page: 1,
      page_size: 200,
      total: 1,
    })
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter>
        <WorkspaceListPage />
        <LocationProbe />
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'باز کردن' }))

    expect(
      screen.getByText('/workspaces/6ab93847-d2b3-43b8-aae1-15662031feb8/entities'),
    ).toBeInTheDocument()
  })
})
