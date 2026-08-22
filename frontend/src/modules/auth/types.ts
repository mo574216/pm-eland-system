export interface WorkspaceSummary {
  id: string
  name: string
}

export interface UserSummary {
  id: string
  username: string
  display_name: string | null
  roles: string[]
}

export interface CurrentUser extends UserSummary {
  permissions: string[]
  workspaces: WorkspaceSummary[]
}

export interface IssuedSession {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: UserSummary
}

export interface LoginCredentials {
  username: string
  password: string
}
