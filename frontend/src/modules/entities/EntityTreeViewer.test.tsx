import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { EntityTreeViewer } from './EntityTreeViewer'
import { getEntityTree, type EntityTreeNode } from './entityApi'

vi.mock('./entityApi', async (importOriginal) => {
  const original = await importOriginal<typeof import('./entityApi')>()
  return { ...original, getEntityTree: vi.fn() }
})

const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'

function node(
  id: string,
  name: string,
  parentId: string | null,
  depth: number,
  hasChildren: boolean,
): EntityTreeNode {
  return {
    id,
    workspace_id: workspaceId,
    entity_type_id: '7ab93847-d2b3-43b8-aae1-15662031feb8',
    entity_type: {
      id: '7ab93847-d2b3-43b8-aae1-15662031feb8',
      key: 'generic_node',
      name: 'Generic Node',
      icon_key: null,
    },
    parent_id: parentId,
    name,
    status: 'ACTIVE',
    depth,
    path: parentId === null ? [id] : [parentId, id],
    has_children: hasChildren,
  }
}

describe('EntityTreeViewer', () => {
  beforeEach(() => vi.mocked(getEntityTree).mockReset())

  it('expands cached roots, lazy-loads deeper children, and selects nodes', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    const root = node('10000000-0000-0000-0000-000000000001', 'Demo Root', null, 0, true)
    const child = node(
      '10000000-0000-0000-0000-000000000002',
      'Demo Child',
      root.id,
      1,
      true,
    )
    const grandchild = node(
      '10000000-0000-0000-0000-000000000003',
      'Demo Grandchild',
      child.id,
      1,
      false,
    )
    vi.mocked(getEntityTree)
      .mockResolvedValueOnce({ items: [root, child], root_id: null, depth: 1 })
      .mockResolvedValueOnce({ items: [{ ...child, depth: 0 }, grandchild], root_id: child.id, depth: 1 })

    renderWithProviders(
      <EntityTreeViewer onSelect={onSelect} workspaceId={workspaceId} />,
    )

    const rootLabel = await screen.findByRole('button', { name: 'Demo Root' })
    expect(screen.queryByText('Demo Child')).not.toBeInTheDocument()
    expect(rootLabel).toBeInTheDocument()
    await user.click(within(screen.getAllByRole('treeitem')[0]).getAllByRole('button')[0])
    const childLabel = await screen.findByRole('button', { name: 'Demo Child' })
    expect(getEntityTree).toHaveBeenCalledTimes(1)

    await user.click(within(screen.getAllByRole('treeitem')[1]).getAllByRole('button')[0])
    expect(await screen.findByText('Demo Grandchild')).toBeInTheDocument()
    expect(getEntityTree).toHaveBeenLastCalledWith(workspaceId, {
      rootId: child.id,
      depth: 1,
    })

    await user.click(childLabel)
    expect(onSelect).toHaveBeenCalledWith(child.id)
  })

  it('offers retry after the initial hierarchy request fails', async () => {
    const user = userEvent.setup()
    const root = node('10000000-0000-0000-0000-000000000001', 'Demo Root', null, 0, false)
    vi.mocked(getEntityTree)
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce({ items: [root], root_id: null, depth: 1 })

    renderWithProviders(
      <EntityTreeViewer onSelect={vi.fn()} workspaceId={workspaceId} />,
    )

    await user.click(await screen.findByRole('button', { name: 'تلاش دوباره' }))
    expect(await screen.findByText('Demo Root')).toBeInTheDocument()
  })
})
