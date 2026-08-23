import { apiRequest } from '../../api/client'

export interface EntityTreeTypeSummary {
  id: string
  key: string
  name: string
  icon_key: string | null
}

export interface EntityTreeNode {
  id: string
  workspace_id: string
  entity_type_id: string
  entity_type: EntityTreeTypeSummary | null
  parent_id: string | null
  name: string
  status: 'ACTIVE' | 'ARCHIVED'
  depth: number
  path: string[]
  has_children: boolean
}

export interface EntityTreeData {
  items: EntityTreeNode[]
  root_id: string | null
  depth: number | null
}

export function getEntityTree(
  workspaceId: string,
  options: { rootId?: string; depth?: number; includeType?: boolean } = {},
): Promise<EntityTreeData> {
  const parameters = new URLSearchParams()
  if (options.rootId !== undefined) parameters.set('root_id', options.rootId)
  if (options.depth !== undefined) parameters.set('depth', String(options.depth))
  parameters.set('include_type', String(options.includeType ?? true))
  return apiRequest<EntityTreeData>(
    `/workspaces/${workspaceId}/entities/tree?${parameters.toString()}`,
  )
}
