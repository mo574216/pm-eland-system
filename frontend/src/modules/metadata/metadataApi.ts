import { apiRequest } from '../../api/client'

export type AttributeDataType =
  | 'TEXT'
  | 'RICH_TEXT'
  | 'INTEGER'
  | 'DECIMAL'
  | 'BOOLEAN'
  | 'DATE'
  | 'DATETIME'
  | 'ENUM'
  | 'MULTI_ENUM'
  | 'USER_REFERENCE'
  | 'ENTITY_REFERENCE'
  | 'FILE_REFERENCE'
  | 'JSON'
  | 'TABLE'

export interface EntityType {
  id: string
  workspace_id: string
  key: string
  name: string
  plural_name: string | null
  description: string | null
  icon_key: string | null
  is_active: boolean
  configuration: Record<string, unknown>
  created_by: string | null
  created_at: string
  updated_at: string
  version: number
}

export interface EntityTypeList {
  items: EntityType[]
  page: number
  page_size: number
  total: number
}

export interface AttributeDefinition {
  id: string
  entity_type_id: string
  key: string
  label: string
  description: string | null
  data_type: AttributeDataType
  is_required: boolean
  is_read_only: boolean
  default_value: unknown
  validation_config: Record<string, unknown>
  display_config: Record<string, unknown>
  inheritance_config: Record<string, unknown>
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
  version: number
}

export interface EntityTypeCreate {
  key: string
  name: string
  plural_name?: string
  description?: string
  configuration: Record<string, unknown>
}

export interface AttributeCreate {
  key: string
  label: string
  data_type: AttributeDataType
  is_required: boolean
  is_read_only: boolean
  display_order: number
  validation_config: Record<string, unknown>
  display_config: Record<string, unknown>
  inheritance_config: Record<string, unknown>
}

export function listEntityTypes(workspaceId: string): Promise<EntityTypeList> {
  return apiRequest<EntityTypeList>(
    `/workspaces/${workspaceId}/entity-types?page=1&page_size=200&active=true`,
  )
}

export function createEntityType(
  workspaceId: string,
  values: EntityTypeCreate,
): Promise<EntityType> {
  return apiRequest<EntityType>(`/workspaces/${workspaceId}/entity-types`, {
    method: 'POST',
    body: JSON.stringify(values),
  })
}

export function getEntityType(entityTypeId: string): Promise<EntityType> {
  return apiRequest<EntityType>(`/entity-types/${entityTypeId}`)
}

export function updateEntityType(
  entityTypeId: string,
  values: Pick<EntityType, 'name' | 'plural_name' | 'description' | 'configuration' | 'version'>,
): Promise<EntityType> {
  return apiRequest<EntityType>(`/entity-types/${entityTypeId}`, {
    method: 'PATCH',
    body: JSON.stringify(values),
  })
}

export function archiveEntityType(entityTypeId: string, version: number): Promise<void> {
  return apiRequest<void>(`/entity-types/${entityTypeId}?version=${String(version)}`, {
    method: 'DELETE',
  })
}

export function listAttributes(entityTypeId: string): Promise<AttributeDefinition[]> {
  return apiRequest<AttributeDefinition[]>(`/entity-types/${entityTypeId}/attributes`)
}

export function createAttribute(
  entityTypeId: string,
  values: AttributeCreate,
): Promise<AttributeDefinition> {
  return apiRequest<AttributeDefinition>(`/entity-types/${entityTypeId}/attributes`, {
    method: 'POST',
    body: JSON.stringify(values),
  })
}

export function deactivateAttribute(attributeId: string, version: number): Promise<void> {
  return apiRequest<void>(`/attributes/${attributeId}?version=${String(version)}`, {
    method: 'DELETE',
  })
}
