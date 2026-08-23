import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { listAttributes } from '../metadata/metadataApi'
import { EntityDetailPage } from './EntityDetailPage'
import { getEntity } from './entityApi'

vi.mock('./entityApi', async (importOriginal) => {
  const original = await importOriginal<typeof import('./entityApi')>()
  return { ...original, getEntity: vi.fn() }
})

vi.mock('../metadata/metadataApi', async (importOriginal) => {
  const original = await importOriginal<typeof import('../metadata/metadataApi')>()
  return { ...original, listAttributes: vi.fn() }
})

const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'
const entityId = '10000000-0000-0000-0000-000000000001'
const entityTypeId = '7ab93847-d2b3-43b8-aae1-15662031feb8'

describe('EntityDetailPage', () => {
  beforeEach(() => {
    vi.mocked(getEntity).mockResolvedValue({
      id: entityId,
      workspace_id: workspaceId,
      entity_type_id: entityTypeId,
      entity_type: {
        id: entityTypeId,
        key: 'generic_node',
        name: 'Generic Node',
        icon_key: null,
      },
      parent_id: null,
      name: 'Demo Root',
      description: 'A metadata-driven entity',
      status: 'ACTIVE',
      attributes: { legacy_score: 12, risk: 'high' },
      created_by: null,
      updated_by: null,
      created_at: '2026-08-23T00:00:00Z',
      updated_at: '2026-08-23T00:00:00Z',
      archived_at: null,
      version: 1,
    })
    vi.mocked(listAttributes).mockResolvedValue([
      {
        id: '8ab93847-d2b3-43b8-aae1-15662031feb8',
        entity_type_id: entityTypeId,
        key: 'risk',
        label: 'Risk level',
        description: null,
        data_type: 'TEXT',
        is_required: false,
        is_read_only: false,
        default_value: null,
        validation_config: {},
        display_config: {},
        inheritance_config: {},
        display_order: 1,
        is_active: true,
        created_at: '2026-08-23T00:00:00Z',
        updated_at: '2026-08-23T00:00:00Z',
        version: 1,
      },
    ])
  })

  it('renders every entity type through the shared tabs and metadata definitions', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${workspaceId}/entities/${entityId}`]}>
        <Routes>
          <Route
            element={<EntityDetailPage />}
            path="/workspaces/:workspaceId/entities/:entityId"
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Demo Root' })).toBeInTheDocument()
    expect(screen.getByText('Generic Node')).toBeInTheDocument()
    expect(screen.getAllByRole('tab')).toHaveLength(6)

    await user.click(screen.getByRole('tab', { name: 'اطلاعات' }))
    expect(await screen.findByText('Risk level')).toBeInTheDocument()
    expect(screen.getByText('high')).toBeInTheDocument()
    expect(screen.getByText('legacy_score')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: 'اسناد' }))
    expect(screen.getByText('این بخش در گام بعدی پیاده‌سازی می‌شود.')).toBeInTheDocument()
  })
})
