import { apiRequest } from '../../api/client'
import type { CurrentUser, IssuedSession, LoginCredentials } from './types'

export function loginRequest(credentials: LoginCredentials): Promise<IssuedSession> {
  return apiRequest<IssuedSession>(
    '/auth/login',
    { method: 'POST', body: JSON.stringify(credentials) },
    { skipAuthRecovery: true },
  )
}

export function refreshRequest(): Promise<IssuedSession> {
  return apiRequest<IssuedSession>(
    '/auth/refresh',
    { method: 'POST' },
    { skipAuthRecovery: true },
  )
}

export function logoutRequest(): Promise<void> {
  return apiRequest<void>('/auth/logout', { method: 'POST' })
}

export function currentUserRequest(): Promise<CurrentUser> {
  return apiRequest<CurrentUser>('/auth/me', {}, { skipAuthRecovery: true })
}
