import { screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { ProtectedRoute } from './ProtectedRoute'

const auth = vi.hoisted(() => ({
  status: 'anonymous',
}))

vi.mock('./authContext', () => ({
  useAuth: () => ({ status: auth.status, user: null, login: vi.fn(), logout: vi.fn() }),
}))

function renderRoutes() {
  return renderWithProviders(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/protected" element={<div>محتوای حفاظت‌شده</div>} />
        </Route>
        <Route path="/login" element={<div>صفحه ورود</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects anonymous users to login', () => {
    auth.status = 'anonymous'
    renderRoutes()
    expect(screen.getByText('صفحه ورود')).toBeInTheDocument()
  })

  it('renders protected content for authenticated users', () => {
    auth.status = 'authenticated'
    renderRoutes()
    expect(screen.getByText('محتوای حفاظت‌شده')).toBeInTheDocument()
  })

  it('shows a session restoration state while initializing', () => {
    auth.status = 'initializing'
    renderRoutes()
    expect(screen.getByLabelText('در حال بررسی نشست کاربری')).toBeInTheDocument()
  })
})
