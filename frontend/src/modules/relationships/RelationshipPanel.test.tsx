import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { listEntities } from '../entities/entityApi'
import { RelationshipPanel } from './RelationshipPanel'
import {
  createRelationship,
  deleteRelationship,
  listRelationships,
  listRelationshipTypes,
} from './relationshipApi'

vi.mock('../entities/entityApi', async (importOriginal) => {
  const original = await importOriginal<typeof import('../entities/entityApi')>()
  return { ...original, listEntities: vi.fn() }
})

vi.mock('./relationshipApi', async (importOriginal) => {
  const original = await importOriginal<typeof import('./relationshipApi')>()
  return {
    ...original,
    createRelationship: vi.fn(),
    deleteRelationship: vi.fn(),
    listRelationships: vi.fn(),
    listRelationshipTypes: vi.fn(),
  }
})

const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'
const entityId = '10000000-0000-0000-0000-000000000001'
const targetId = '10000000-0000-0000-0000-000000000002'
const typeId = '20000000-0000-0000-0000-000000000001'
const otherTypeId = '20000000-0000-0000-0000-000000000002'
const relationshipId = '30000000-0000-0000-0000-000000000001'

describe('RelationshipPanel', () => {
  beforeEach(() => {
    vi.mocked(listRelationshipTypes).mockResolvedValue({
      items: [
        {
          id: typeId,
          workspace_id: workspaceId,
          key: 'depends_on',
          name: 'Depends On',
          description: null,
          directionality: 'DIRECTED',
          source_type_id: null,
          target_type_id: null,
          configuration: { allow_duplicates: false },
          is_active: true,
          created_at: '2026-08-23T00:00:00Z',
        },
        {
          id: otherTypeId,
          workspace_id: workspaceId,
          key: 'hosts',
          name: 'Hosts',
          description: null,
          directionality: 'DIRECTED',
          source_type_id: otherTypeId,
          target_type_id: null,
          configuration: {},
          is_active: true,
          created_at: '2026-08-23T00:00:00Z',
        },
      ],
      page: 1,
      page_size: 200,
      total: 1,
    })
    vi.mocked(listEntities).mockResolvedValue({
      items: [
        {
          id: entityId,
          workspace_id: workspaceId,
          entity_type_id: typeId,
          entity_type: { id: typeId, key: 'node', name: 'Node', icon_key: null },
          parent_id: null,
          name: 'Demo Root',
          description: null,
          status: 'ACTIVE',
          attributes: {},
          created_by: null,
          updated_by: null,
          created_at: '2026-08-23T00:00:00Z',
          updated_at: '2026-08-23T00:00:00Z',
          archived_at: null,
          version: 1,
        },
        {
          id: targetId,
          workspace_id: workspaceId,
          entity_type_id: typeId,
          entity_type: { id: typeId, key: 'node', name: 'Node', icon_key: null },
          parent_id: null,
          name: 'Second Root',
          description: null,
          status: 'ACTIVE',
          attributes: {},
          created_by: null,
          updated_by: null,
          created_at: '2026-08-23T00:00:00Z',
          updated_at: '2026-08-23T00:00:00Z',
          archived_at: null,
          version: 1,
        },
      ],
      page: 1,
      page_size: 200,
      total: 2,
    })
    vi.mocked(listRelationships).mockResolvedValue({
      items: [
        {
          id: relationshipId,
          workspace_id: workspaceId,
          relationship_type_id: typeId,
          source_entity_id: entityId,
          target_entity_id: targetId,
          attributes: {},
          created_by: null,
          created_at: '2026-08-23T00:00:00Z',
        },
      ],
      page: 1,
      page_size: 200,
      total: 1,
    })
    vi.mocked(createRelationship).mockResolvedValue({
      id: '30000000-0000-0000-0000-000000000002',
      workspace_id: workspaceId,
      relationship_type_id: typeId,
      source_entity_id: entityId,
      target_entity_id: targetId,
      attributes: {},
      created_by: null,
      created_at: '2026-08-23T00:00:00Z',
    })
    vi.mocked(deleteRelationship).mockResolvedValue(undefined)
  })

  it('shows named relationships and supports generic create and delete actions', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <RelationshipPanel canManage entityId={entityId} workspaceId={workspaceId} />,
    )

    expect(await screen.findByText('Demo Root Depends On Second Root')).toBeInTheDocument()
    expect(screen.queryByText('خروجی')).not.toBeInTheDocument()

    await user.click(screen.getByRole('combobox', { name: 'چه ارتباطی دارد؟' }))
    expect(screen.queryByRole('option', { name: 'Hosts' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('option', { name: 'Depends On' }))
    await user.click(screen.getByRole('combobox', { name: 'با کدام مورد؟' }))
    await user.click(screen.getByRole('option', { name: 'Second Root — Node' }))
    await user.click(screen.getByRole('button', { name: 'ایجاد رابطه' }))
    expect(createRelationship).toHaveBeenCalledWith(workspaceId, {
      relationship_type_id: typeId,
      source_entity_id: entityId,
      target_entity_id: targetId,
    })

    await user.click(screen.getByRole('button', { name: 'حذف رابطه' }))
    expect(deleteRelationship).toHaveBeenCalledWith(relationshipId)
  })
})
