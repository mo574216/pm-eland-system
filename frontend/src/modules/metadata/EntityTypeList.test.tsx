import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { EntityTypeList } from './EntityTypeList'
import { createEntityType, listEntityTypes } from './metadataApi'

vi.mock('./metadataApi', () => ({
  createEntityType: vi.fn(),
  listEntityTypes: vi.fn(),
}))

const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'
const entityType = {
  id: '7ab93847-d2b3-43b8-aae1-15662031feb8',
  workspace_id: workspaceId,
  key: 'business_process',
  name: 'Business Process',
  plural_name: 'Business Processes',
  description: null,
  icon_key: null,
  is_active: true,
  configuration: {},
  created_by: null,
  created_at: '2026-08-22T00:00:00Z',
  updated_at: '2026-08-22T00:00:00Z',
  version: 1,
}

describe('EntityTypeList', () => {
  beforeEach(() => {
    vi.mocked(listEntityTypes).mockResolvedValue({
      items: [entityType],
      page: 1,
      page_size: 200,
      total: 1,
    })
    vi.mocked(createEntityType).mockResolvedValue(entityType)
  })

  it('lists metadata and creates an arbitrary entity type', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${workspaceId}/metadata`]}>
        <Routes>
          <Route path="/workspaces/:workspaceId/metadata" element={<EntityTypeList />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Business Process')).toBeInTheDocument()
    const fields = screen.getAllByRole('textbox')
    await user.type(fields[0], 'network_security_zone')
    await user.type(fields[1], 'Network Security Zone')
    await user.click(screen.getByRole('button', { name: 'ایجاد نوع موجودیت' }))

    expect(createEntityType).toHaveBeenCalledWith(workspaceId, {
      key: 'network_security_zone',
      name: 'Network Security Zone',
      plural_name: undefined,
      description: undefined,
      configuration: {},
    })
  })
})
