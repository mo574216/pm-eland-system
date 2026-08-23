import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { DocumentPanel } from './DocumentPanel'
import {
  listDocumentVersions,
  listEntityDocuments,
  getDocumentPreview,
  uploadDocument,
} from './documentApi'
import type { Document, DocumentVersion } from './types'

vi.mock('./documentApi', () => ({
  getDocumentDownload: vi.fn(),
  getDocumentPreview: vi.fn(),
  listDocumentVersions: vi.fn(),
  listEntityDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  uploadDocumentVersion: vi.fn(),
}))

const version: DocumentVersion = {
  id: '20000000-0000-0000-0000-000000000001',
  document_id: '10000000-0000-0000-0000-000000000001',
  version_number: 1,
  original_file_name: 'architecture.pdf',
  content_type: 'application/pdf',
  file_extension: '.pdf',
  file_size_bytes: 1024,
  checksum_sha256: null,
  scan_status: 'CLEAN',
  preview_status: 'READY',
  uploaded_by: null,
  uploaded_at: '2026-08-23T00:00:00Z',
  comment: 'نسخه نخست',
  metadata: {},
}

const document: Document = {
  id: version.document_id,
  workspace_id: '30000000-0000-0000-0000-000000000001',
  entity_id: '40000000-0000-0000-0000-000000000001',
  title: 'گزارش معماری',
  description: null,
  document_type: 'REPORT',
  lifecycle_status: 'ACTIVE',
  current_version_id: version.id,
  current_version: version,
  created_by: null,
  created_at: '2026-08-23T00:00:00Z',
  updated_at: '2026-08-23T00:00:00Z',
}

describe('DocumentPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listEntityDocuments).mockResolvedValue({ items: [document], page: 1, page_size: 100, total: 1 })
    vi.mocked(listDocumentVersions).mockResolvedValue({ items: [version], page: 1, page_size: 100, total: 1 })
    vi.mocked(uploadDocument).mockResolvedValue({
      document_id: document.id,
      version_id: version.id,
      version_number: 1,
      scan_status: 'PENDING',
    })
    vi.mocked(getDocumentPreview).mockResolvedValue({
      status: 'READY',
      preview_type: 'PDF',
      url: 'https://storage.test/preview.pdf',
      expires_at: '2026-08-23T00:10:00Z',
    })
  })

  it('shows immutable history and uploads a new logical document', async () => {
    const user = userEvent.setup()
    renderWithProviders(<DocumentPanel canRead canUpload entityId={document.entity_id ?? ''} />)

    expect(await screen.findByRole('heading', { name: document.title })).toBeVisible()
    expect(screen.getByText('پاک')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'تاریخچه نسخه‌ها' }))
    expect(await screen.findByText(version.original_file_name, { exact: false })).toBeVisible()
    expect(screen.getByText(version.comment ?? '')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'پیش‌نمایش' }))
    expect(getDocumentPreview).toHaveBeenCalled()
    expect(vi.mocked(getDocumentPreview).mock.calls[0]?.[0]).toBe(version.id)
    expect(await screen.findByTitle('پیش‌نمایش PDF')).toHaveAttribute(
      'src',
      'https://storage.test/preview.pdf',
    )
    await user.click(screen.getByRole('button', { name: 'بستن پیش‌نمایش' }))

    await user.type(screen.getByLabelText(/عنوان سند/), 'سند جدید')
    const file = new File(['%PDF-1.7\ntest'], 'new-report.pdf', { type: 'application/pdf' })
    await user.upload(screen.getByTestId('new-document-file'), file)
    await user.click(screen.getByRole('button', { name: 'بارگذاری سند' }))

    expect(uploadDocument).toHaveBeenCalledWith(document.entity_id, {
      file,
      title: 'سند جدید',
      description: '',
      documentType: '',
    })
  }, 10_000)
})
