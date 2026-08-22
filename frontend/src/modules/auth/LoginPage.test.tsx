import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { renderWithProviders } from '../../test/render'
import { LoginPage } from './LoginPage'

const auth = vi.hoisted(() => ({
  login: vi.fn(),
  logout: vi.fn(),
}))

vi.mock('./authContext', () => ({
  useAuth: () => ({
    status: 'anonymous',
    user: null,
    login: auth.login,
    logout: auth.logout,
  }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    auth.login.mockReset()
  })

  it('submits accessible username and password fields', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/نام کاربری/), 'analyst1')
    await user.type(screen.getByLabelText(/گذرواژه/), 'correct-password')
    await user.click(screen.getByRole('button', { name: 'ورود' }))

    expect(auth.login).toHaveBeenCalledWith({
      username: 'analyst1',
      password: 'correct-password',
    })
  })

  it('shows a safe message for invalid credentials', async () => {
    auth.login.mockRejectedValueOnce(new ApiError(401, 'AUTH_INVALID_CREDENTIALS'))
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/نام کاربری/), 'analyst1')
    await user.type(screen.getByLabelText(/گذرواژه/), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'ورود' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'نام کاربری یا گذرواژه نادرست است.',
    )
  })

  it('requires both credential fields', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: 'ورود' }))

    expect(await screen.findByText('وارد کردن نام کاربری الزامی است.')).toBeInTheDocument()
    expect(screen.getByText('وارد کردن گذرواژه الزامی است.')).toBeInTheDocument()
    expect(auth.login).not.toHaveBeenCalled()
  })
})
