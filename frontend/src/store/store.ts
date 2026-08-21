import { configureStore, createSlice, type PayloadAction } from '@reduxjs/toolkit'

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

export const store = configureStore({
  reducer: { ui: uiSlice.reducer },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
