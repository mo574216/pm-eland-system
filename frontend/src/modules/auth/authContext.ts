import { createContext, useContext } from 'react'

import type { AuthStatus } from './authSlice'
import type { CurrentUser, LoginCredentials } from './types'

export interface AuthContextValue {
  status: AuthStatus
  user: CurrentUser | null
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth must be used within AuthProvider.')
  }
  return context
}
