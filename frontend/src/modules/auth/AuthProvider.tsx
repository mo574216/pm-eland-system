import { type PropsWithChildren, useCallback, useEffect, useMemo, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { setApiAccessToken, setAuthRecoveryHandler } from '../../api/client'
import type { AppDispatch, RootState } from '../../store/store'
import { currentUserRequest, loginRequest, logoutRequest, refreshRequest } from './authApi'
import { AuthContext } from './authContext'
import { sessionAuthenticated, sessionCleared } from './authSlice'
import type { IssuedSession, LoginCredentials } from './types'

export function AuthProvider({ children }: PropsWithChildren) {
  const dispatch = useDispatch<AppDispatch>()
  const { status, user } = useSelector((state: RootState) => state.auth)
  const refreshInFlight = useRef<Promise<boolean> | null>(null)

  const clearSession = useCallback(() => {
    setApiAccessToken(null)
    dispatch(sessionCleared())
  }, [dispatch])

  const establishSession = useCallback(
    async (session: IssuedSession): Promise<void> => {
      setApiAccessToken(session.access_token)
      try {
        const currentUser = await currentUserRequest()
        dispatch(sessionAuthenticated(currentUser))
      } catch (error) {
        clearSession()
        throw error
      }
    },
    [clearSession, dispatch],
  )

  const recoverSession = useCallback((): Promise<boolean> => {
    if (refreshInFlight.current !== null) {
      return refreshInFlight.current
    }

    const recovery = refreshRequest()
      .then(async (session) => {
        await establishSession(session)
        return true
      })
      .catch(() => {
        clearSession()
        return false
      })
      .finally(() => {
        refreshInFlight.current = null
      })

    refreshInFlight.current = recovery
    return recovery
  }, [clearSession, establishSession])

  useEffect(() => {
    setAuthRecoveryHandler(recoverSession)
    void recoverSession()

    return () => {
      setAuthRecoveryHandler(null)
      setApiAccessToken(null)
    }
  }, [recoverSession])

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const session = await loginRequest(credentials)
      await establishSession(session)
    },
    [establishSession],
  )

  const logout = useCallback(async () => {
    await logoutRequest()
    clearSession()
  }, [clearSession])

  const value = useMemo(
    () => ({ status, user, login, logout }),
    [status, user, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
