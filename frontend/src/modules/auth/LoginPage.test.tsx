import { screen } from '@testing-library/react'

import { renderWithProviders } from '../../test/render'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
  it('renders accessible credential fields with submission disabled', () => {
    renderWithProviders(<LoginPage />)

    expect(screen.getByRole('heading', { name: 'ورود' })).toBeInTheDocument()
    expect(screen.getByLabelText(/ایمیل/)).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText(/گذرواژه/)).toHaveAttribute('type', 'password')
    expect(screen.getByRole('button', { name: 'ورود' })).toBeDisabled()
  })
})
