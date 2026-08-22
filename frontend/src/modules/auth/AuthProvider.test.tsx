import { screen } from '@testing-library/react'
import { Provider as ReduxProvider } from 'react-redux'

import { createAppStore } from '../../store/store'
import { renderWithProviders } from '../../test/render'
import { currentUserRequest, refreshRequest } from './authApi'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './authContext'

vi.mock('./authApi', () => ({
  currentUserRequest: vi.fn(),
  loginRequest: vi.fn(),
  logoutRequest: vi.fn(),
  refreshRequest: vi.fn(),
}))

const issuedSession = {
  access_token: 'access-token',
  token_type: 'bearer' as const,
  expires_in: 900,
  user: {
    id: '7a2cf874-79e5-4cea-a20e-7a086f3ce905',
    username: 'analyst1',
    display_name: 'تحلیلگر یک',
    roles: ['ANALYST'],
  },
}

const currentUser = {
  ...issuedSession.user,
  permissions: ['ENTITY_READ'],
  workspaces: [],
}

function AuthObserver() {
  const { status, user } = useAuth()
  return <div>{status === 'authenticated' ? user?.display_name : status}</div>
}

function renderProvider() {
  const store = createAppStore()
  return renderWithProviders(
    <ReduxProvider store={store}>
      <AuthProvider>
        <AuthObserver />
      </AuthProvider>
    </ReduxProvider>,
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.mocked(currentUserRequest).mockReset()
    vi.mocked(refreshRequest).mockReset()
  })

  it('restores the user context through the refresh cookie on startup', async () => {
    vi.mocked(refreshRequest).mockResolvedValue(issuedSession)
    vi.mocked(currentUserRequest).mockResolvedValue(currentUser)

    renderProvider()

    expect(await screen.findByText('تحلیلگر یک')).toBeInTheDocument()
    expect(refreshRequest).toHaveBeenCalledOnce()
    expect(currentUserRequest).toHaveBeenCalledOnce()
  })

  it('becomes anonymous when no refresh session exists', async () => {
    vi.mocked(refreshRequest).mockRejectedValue(new Error('no session'))

    renderProvider()

    expect(await screen.findByText('anonymous')).toBeInTheDocument()
    expect(currentUserRequest).not.toHaveBeenCalled()
  })
})
