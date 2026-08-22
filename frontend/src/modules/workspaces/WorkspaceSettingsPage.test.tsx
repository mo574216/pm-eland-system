import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { WorkspaceSettingsPage } from './WorkspaceSettingsPage'
import {
  getWorkspace,
  listWorkspaceMembers,
  updateWorkspace,
} from './workspaceApi'

vi.mock('./workspaceApi', () => ({
  addWorkspaceMember: vi.fn(),
  getWorkspace: vi.fn(),
  listWorkspaceMembers: vi.fn(),
  removeWorkspaceMember: vi.fn(),
  updateWorkspace: vi.fn(),
}))

const workspace = {
  id: '6ab93847-d2b3-43b8-aae1-15662031feb8',
  name: 'فضای اصلی',
  slug: 'main-workspace',
  description: 'شرح اولیه',
  owner_id: null,
  status: 'ACTIVE' as const,
  configuration: {},
  created_at: '2026-08-22T00:00:00Z',
  updated_at: '2026-08-22T00:00:00Z',
  archived_at: null,
  version: 3,
}

describe('WorkspaceSettingsPage', () => {
  beforeEach(() => {
    vi.mocked(getWorkspace).mockResolvedValue(workspace)
    vi.mocked(listWorkspaceMembers).mockResolvedValue([])
    vi.mocked(updateWorkspace).mockResolvedValue({ ...workspace, name: 'نام تازه', version: 4 })
  })

  it('saves mutable fields with the loaded version', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${workspace.id}/settings`]}>
        <Routes>
          <Route path="/workspaces/:workspaceId/settings" element={<WorkspaceSettingsPage />} />
        </Routes>
      </MemoryRouter>,
    )

    const name = await screen.findByLabelText(/نام فضای کاری/)
    await user.clear(name)
    await user.type(name, 'نام تازه')
    await user.click(screen.getByRole('button', { name: 'ذخیره تغییرات' }))

    expect(updateWorkspace).toHaveBeenCalledWith(workspace.id, {
      name: 'نام تازه',
      description: 'شرح اولیه',
      version: 3,
    })
    expect(await screen.findByRole('alert')).toHaveTextContent('تغییرات ذخیره شد.')
  })
})
