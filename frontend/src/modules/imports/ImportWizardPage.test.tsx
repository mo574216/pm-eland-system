import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { uploadImport } from './importApi'
import { ImportWizardPage } from './ImportWizardPage'

vi.mock('./importApi', () => ({ uploadImport: vi.fn() }))

const mockedUpload = vi.mocked(uploadImport)

describe('ImportWizardPage', () => {
  it('uploads a CSV and displays real inspection metadata', async () => {
    mockedUpload.mockResolvedValue({
      import_job_id: 'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      status: 'UPLOADED',
      sheets: [
        {
          name: 'people.csv',
          row_count: 2,
          columns: [
            { name: 'Name', sample_values: ['Ali', 'Sara'] },
            { name: 'Score', sample_values: ['4', '5'] },
          ],
        },
      ],
    })
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={['/workspaces/workspace-1/imports']}>
        <Routes>
          <Route path="/workspaces/:workspaceId/imports" element={<ImportWizardPage />} />
        </Routes>
      </MemoryRouter>,
    )

    const file = new File(['Name,Score\nAli,4\nSara,5'], 'people.csv', { type: 'text/csv' })
    await user.upload(screen.getByLabelText('انتخاب فایل'), file)
    await user.click(screen.getByRole('button', { name: 'بارگذاری و بررسی' }))

    expect(await screen.findByText('people.csv')).toBeVisible()
    expect(screen.getByText('Name')).toBeVisible()
    expect(screen.getByText('Ali، Sara')).toBeVisible()
    expect(mockedUpload).toHaveBeenCalledWith('workspace-1', file)
    expect(screen.getByText(/هیچ داده اصلی تغییر نکرده است/)).toBeVisible()
  })
})
