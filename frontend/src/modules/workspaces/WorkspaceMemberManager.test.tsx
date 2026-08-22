import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { WorkspaceMemberManager } from './WorkspaceMemberManager'
import {
  addWorkspaceMember,
  listWorkspaceMembers,
  removeWorkspaceMember,
} from './workspaceApi'

vi.mock('./workspaceApi', () => ({
  addWorkspaceMember: vi.fn(),
  listWorkspaceMembers: vi.fn(),
  removeWorkspaceMember: vi.fn(),
}))

const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'
const userId = '38f186da-6259-420f-98ff-024055f42140'
const roleId = '233f9764-03b4-4b01-a9bb-76ee894bfc97'

describe('WorkspaceMemberManager', () => {
  beforeEach(() => {
    vi.mocked(listWorkspaceMembers).mockResolvedValue([])
    vi.mocked(addWorkspaceMember).mockResolvedValue({
      id: '06e9e0d9-262a-428b-809d-fd14c6960567',
      user_id: userId,
      username: 'analyst1',
      display_name: 'تحلیلگر',
      role_id: roleId,
      role_code: 'ANALYST',
      status: 'ACTIVE',
      created_at: '2026-08-22T00:00:00Z',
    })
    vi.mocked(removeWorkspaceMember).mockResolvedValue()
  })

  it('adds a member using the contract identifiers', async () => {
    const user = userEvent.setup()
    renderWithProviders(<WorkspaceMemberManager workspaceId={workspaceId} />)

    await user.type(screen.getByLabelText('شناسه کاربر'), userId)
    await user.type(screen.getByLabelText('شناسه نقش'), roleId)
    await user.click(screen.getByRole('button', { name: 'افزودن عضو' }))

    expect(addWorkspaceMember).toHaveBeenCalledWith(workspaceId, {
      user_id: userId,
      role_id: roleId,
    })
  })

  it('removes a listed member through the scoped endpoint', async () => {
    vi.mocked(listWorkspaceMembers).mockResolvedValue([
      {
        id: '06e9e0d9-262a-428b-809d-fd14c6960567',
        user_id: userId,
        username: 'analyst1',
        display_name: 'تحلیلگر',
        role_id: roleId,
        role_code: 'ANALYST',
        status: 'ACTIVE',
        created_at: '2026-08-22T00:00:00Z',
      },
    ])
    const user = userEvent.setup()
    renderWithProviders(<WorkspaceMemberManager workspaceId={workspaceId} />)

    await user.click(await screen.findByRole('button', { name: 'حذف عضو' }))

    expect(removeWorkspaceMember).toHaveBeenCalledWith(workspaceId, userId)
  })
})
