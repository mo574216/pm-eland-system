import { apiRequest } from '../../api/client'

export interface RelationshipType {
  id: string
  workspace_id: string
  key: string
  name: string
  description: string | null
  directionality: 'DIRECTED' | 'UNDIRECTED'
  source_type_id: string | null
  target_type_id: string | null
  configuration: Record<string, unknown>
  is_active: boolean
  created_at: string
}

export interface RelationshipTypeList {
  items: RelationshipType[]
  page: number
  page_size: number
  total: number
}

export interface EntityRelationship {
  id: string
  workspace_id: string
  relationship_type_id: string
  source_entity_id: string
  target_entity_id: string
  attributes: Record<string, unknown>
  created_by: string | null
  created_at: string
}

export interface RelationshipList {
  items: EntityRelationship[]
  page: number
  page_size: number
  total: number
}

export function listRelationshipTypes(workspaceId: string): Promise<RelationshipTypeList> {
  return apiRequest<RelationshipTypeList>(
    `/workspaces/${workspaceId}/relationship-types?page=1&page_size=200`,
  )
}

export function listRelationships(entityId: string): Promise<RelationshipList> {
  return apiRequest<RelationshipList>(
    `/entities/${entityId}/relationships?direction=both&page=1&page_size=200`,
  )
}

export function createRelationship(
  workspaceId: string,
  values: {
    relationship_type_id: string
    source_entity_id: string
    target_entity_id: string
  },
): Promise<EntityRelationship> {
  return apiRequest<EntityRelationship>(`/workspaces/${workspaceId}/relationships`, {
    method: 'POST',
    body: JSON.stringify({ ...values, attributes: {} }),
  })
}

export function deleteRelationship(relationshipId: string): Promise<void> {
  return apiRequest<void>(`/relationships/${relationshipId}`, { method: 'DELETE' })
}
