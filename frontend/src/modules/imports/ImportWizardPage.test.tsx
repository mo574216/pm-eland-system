import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import {
  assignImportProfile,
  commitImport,
  createImportProfile,
  dryRunImport,
  resolveImportConflict,
  uploadImport,
} from './importApi'
import { ImportWizard, ImportWizardPage } from './ImportWizardPage'

vi.mock('./importApi', () => ({
  uploadImport: vi.fn(),
  commitImport: vi.fn(),
  createImportProfile: vi.fn(),
  listImportProfiles: vi.fn().mockResolvedValue({ items: [], page: 1, page_size: 200, total: 0 }),
  assignImportProfile: vi.fn().mockResolvedValue({
    import_job_id: 'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
    status: 'UPLOADED',
    import_profile_id: 'profile-1',
  }),
  dryRunImport: vi.fn(),
  listImportConflicts: vi.fn().mockResolvedValue({
    items: [{
      id: 'conflict-1',
      import_job_id: 'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      row_number: 2,
      entity_id: 'entity-1',
      attribute_key: 'name',
      existing_value: 'علی',
      imported_value: 'علی رضایی',
      resolution: null,
    }],
    page: 1,
    page_size: 25,
    total: 1,
    unresolved: 1,
  }),
  resolveImportConflict: vi.fn(),
  resolveImportConflictsBulk: vi.fn(),
}))
vi.mock('../metadata/metadataApi', () => ({
  listEntityTypes: vi.fn().mockResolvedValue({
    items: [{ id: 'entity-type-1', name: 'افراد' }], page: 1, page_size: 200, total: 1,
  }),
  listAttributes: vi.fn().mockResolvedValue([]),
}))

const mockedUpload = vi.mocked(uploadImport)
const mockedCreateProfile = vi.mocked(createImportProfile)
const mockedAssignProfile = vi.mocked(assignImportProfile)
const mockedDryRun = vi.mocked(dryRunImport)
const mockedResolveConflict = vi.mocked(resolveImportConflict)
const mockedCommit = vi.mocked(commitImport)

describe('ImportWizardPage', () => {
  it('renders as an embeddable workflow with contextual heading', () => {
    renderWithProviders(
      <ImportWizard
        description="ورود خروجی این مرحله"
        title="ورود مشخصات فرایند"
        workspaceId="workspace-1"
      />,
    )

    expect(screen.getByRole('heading', { name: 'ورود مشخصات فرایند' })).toBeVisible()
    expect(screen.getByText('ورود خروجی این مرحله')).toBeVisible()
  })

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

    expect(await screen.findByRole('heading', { name: 'people.csv' })).toBeVisible()
    expect(screen.getByText('Name')).toBeVisible()
    expect(screen.getByText('Ali، Sara')).toBeVisible()
    expect(mockedUpload).toHaveBeenCalledWith('workspace-1', file)
    expect(screen.getByText(/هیچ داده اصلی تغییر نکرده است/)).toBeVisible()
    expect(screen.getByRole('heading', { name: 'نگاشت ستون‌ها و شناسایی رکوردها' })).toBeVisible()

    await user.click(screen.getByLabelText('نوع موجودیت مقصد'))
    await user.click(screen.getByRole('option', { name: 'افراد' }))
    await user.type(screen.getByLabelText('نام پروفایل ورود'), 'ورود افراد')
    await user.click(screen.getByLabelText('Name ← فیلد مقصد'))
    await user.click(screen.getByRole('option', { name: 'نام موجودیت' }))
    await user.click(screen.getByLabelText('ستون‌های کلید'))
    await user.click(screen.getByRole('option', { name: /Name/ }))
    mockedCreateProfile.mockResolvedValue({
      id: 'profile-1',
      entity_type_id: 'entity-type-1',
      name: 'ورود افراد',
      source_type: 'CSV',
      matching_strategy: {
        type: 'UNIQUE_ATTRIBUTE',
        key: { source_sheet: 'people.csv', source_column: 'Name', system_field: 'name' },
      },
      mappings: [{
        source_sheet: 'people.csv', source_column: 'Name', target_system_field: 'name',
        transformation_config: {}, display_order: 0,
      }],
    })
    await user.click(screen.getByRole('button', { name: 'ذخیره نگاشت و ادامه' }))

    expect(await screen.findByText(/پروفایل «ورود افراد» ذخیره شد/)).toBeVisible()
    expect(mockedCreateProfile).toHaveBeenCalledWith(
      'workspace-1',
      expect.objectContaining({ entity_type_id: 'entity-type-1', name: 'ورود افراد' }),
    )
    expect(mockedAssignProfile).toHaveBeenCalledWith(
      'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      'profile-1',
    )

    mockedDryRun.mockResolvedValue({
      import_job_id: 'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      status: 'READY_FOR_REVIEW',
      summary: {
        rows_read: 2,
        rows_valid: 2,
        rows_invalid: 0,
        records_to_create: 1,
        records_to_update: 1,
        records_unchanged: 0,
        conflicts: 1,
      },
      validation_errors: [],
    })
    await user.click(screen.getByRole('button', { name: 'اجرای آزمایشی و نمایش نتیجه' }))

    expect(await screen.findByRole('heading', { name: 'نتیجه اجرای آزمایشی' })).toBeVisible()
    expect(screen.getByText('آماده بررسی')).toBeVisible()
    expect(screen.getByText('هیچ موجودیتی ایجاد یا تغییر نکرده است.', { exact: false })).toBeVisible()
    expect(await screen.findByRole('heading', { name: 'بررسی و رفع تعارض‌ها' })).toBeVisible()
    expect(screen.getByText('علی رضایی')).toBeVisible()

    mockedResolveConflict.mockResolvedValue({
      import_job_id: 'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      status: 'READY_TO_COMMIT',
      resolved: 1,
      unresolved: 0,
    })
    await user.click(screen.getByRole('button', { name: 'ادغام' }))

    expect(await screen.findByText(/همه تعارض‌ها تصمیم‌گیری شده‌اند/)).toBeVisible()
    expect(mockedResolveConflict).toHaveBeenCalledWith(
      'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      'conflict-1',
      'MERGE',
    )

    mockedCommit.mockResolvedValue({
      import_job_id: 'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      status: 'COMPLETED',
      summary: {
        rows_read: 2,
        records_created: 1,
        records_updated: 1,
        records_unchanged: 0,
        records_skipped: 0,
        conflicts_resolved: 1,
        invalid_rows: 0,
      },
    })
    await user.click(screen.getByRole('button', { name: 'بررسی و تأیید نهایی' }))
    expect(screen.getByRole('dialog', { name: 'تأیید نهایی ورود اطلاعات' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'تأیید و ثبت نهایی' }))

    expect(await screen.findByText('ورود اطلاعات با موفقیت انجام شد.')).toBeVisible()
    expect(screen.getByText('رکوردهای ایجادشده: ۱')).toBeVisible()
    expect(mockedCommit).toHaveBeenCalledWith(
      'f1cb5ce2-64b5-4726-a653-acb73af7e9cc',
      expect.any(String),
    )
  }, 15_000)
})
