import { screen } from '@testing-library/react'

import { renderWithProviders } from '../../test/render'
import { WorkspaceListPage } from './WorkspaceListPage'

describe('WorkspaceListPage', () => {
  it('shows the workspace heading and API placeholder', () => {
    renderWithProviders(<WorkspaceListPage />)

    expect(screen.getByRole('heading', { name: 'Workspaces' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('workspace API')
  })
})
