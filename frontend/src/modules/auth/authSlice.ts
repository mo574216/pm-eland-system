import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { CurrentUser } from './types'

export type AuthStatus = 'initializing' | 'anonymous' | 'authenticated'

export interface AuthState {
  status: AuthStatus
  user: CurrentUser | null
}

const initialState: AuthState = {
  status: 'initializing',
  user: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    sessionAuthenticated(state, action: PayloadAction<CurrentUser>) {
      state.status = 'authenticated'
      state.user = action.payload
    },
    sessionCleared(state) {
      state.status = 'anonymous'
      state.user = null
    },
  },
})

export const { sessionAuthenticated, sessionCleared } = authSlice.actions
export const authReducer = authSlice.reducer
