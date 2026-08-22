import { configureStore, createSlice, type PayloadAction } from '@reduxjs/toolkit'

import { authReducer } from '../modules/auth/authSlice'

interface UiState {
  selectedWorkspaceId: string | null
}

const initialState: UiState = { selectedWorkspaceId: null }

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    workspaceSelected(state, action: PayloadAction<string | null>) {
      state.selectedWorkspaceId = action.payload
    },
  },
})

export const { workspaceSelected } = uiSlice.actions

export function createAppStore() {
  return configureStore({
    reducer: { auth: authReducer, ui: uiSlice.reducer },
  })
}

export const store = createAppStore()

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
