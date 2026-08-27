import { apiRequest } from '../../api/client'

export interface Workspace {
  id: string
  name: string
  slug: string
  description: string | null
  owner_id: string | null
  status: 'DRAFT' | 'ACTIVE' | 'ARCHIVED'
  configuration: Record<string, unknown>
  created_at: string
  updated_at: string
  archived_at: string | null
  version: number
}

export interface WorkspaceList {
  items: Workspace[]
  page: number
  page_size: number
  total: number
}

export interface WorkspaceMember {
  id: string
  user_id: string
  username: string
  display_name: string | null
  role_id: string | null
  role_code: string | null
  role_name?: string | null
  role_description?: string | null
  status: 'ACTIVE' | 'SUSPENDED'
  created_at: string
}

export interface WorkspaceMemberCreate {
  user_id: string
  role_id: string
}

export interface WorkspacePersonOption {
  id: string
  username: string
  display_name: string | null
}

export interface WorkspaceRoleOption {
  id: string
  code: string
  name: string
  description: string | null
}

export function listWorkspaces(): Promise<WorkspaceList> {
  return apiRequest<WorkspaceList>('/workspaces?page=1&page_size=200')
}

export function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiRequest<Workspace>(`/workspaces/${workspaceId}`)
}

export function updateWorkspace(
  workspaceId: string,
  values: { name: string; description: string | null; version: number },
): Promise<Workspace> {
  return apiRequest<Workspace>(`/workspaces/${workspaceId}`, {
    method: 'PATCH',
    body: JSON.stringify(values),
  })
}

export function listWorkspaceMembers(workspaceId: string): Promise<WorkspaceMember[]> {
  return apiRequest<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`)
}

export function searchWorkspaceMemberOptions(
  workspaceId: string,
  search: string,
): Promise<WorkspacePersonOption[]> {
  const query = new URLSearchParams({ search, limit: '10' })
  return apiRequest<WorkspacePersonOption[]>(
    `/workspaces/${workspaceId}/member-options?${query.toString()}`,
  )
}

export function listWorkspaceRoleOptions(workspaceId: string): Promise<WorkspaceRoleOption[]> {
  return apiRequest<WorkspaceRoleOption[]>(`/workspaces/${workspaceId}/role-options`)
}

export function addWorkspaceMember(
  workspaceId: string,
  values: WorkspaceMemberCreate,
): Promise<WorkspaceMember> {
  return apiRequest<WorkspaceMember>(`/workspaces/${workspaceId}/members`, {
    method: 'POST',
    body: JSON.stringify(values),
  })
}

export function removeWorkspaceMember(workspaceId: string, userId: string): Promise<void> {
  return apiRequest<void>(`/workspaces/${workspaceId}/members/${userId}`, {
    method: 'DELETE',
  })
}
