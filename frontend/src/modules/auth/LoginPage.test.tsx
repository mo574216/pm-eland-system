import { screen } from '@testing-library/react'

import { renderWithProviders } from '../../test/render'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
  it('renders accessible credential fields with submission disabled', () => {
    renderWithProviders(<LoginPage />)

    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/)).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText(/Password/)).toHaveAttribute('type', 'password')
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeDisabled()
  })
})
