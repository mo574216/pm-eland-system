import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { listAttributes, listEntityTypes } from '../metadata/metadataApi'
import { FormDesignerPage } from './FormDesignerPage'
import {
  createNewFormVersion,
  getForm,
  listForms,
  publishForm,
  updateFormSections,
} from './formApi'
import type { FormDefinition } from './types'

vi.mock('../metadata/metadataApi', () => ({
  listAttributes: vi.fn(),
  listEntityTypes: vi.fn(),
}))

vi.mock('./formApi', () => ({
  addFormField: vi.fn(),
  createForm: vi.fn(),
  createNewFormVersion: vi.fn(),
  getForm: vi.fn(),
  listForms: vi.fn(),
  publishForm: vi.fn(),
  updateFormSections: vi.fn(),
}))

vi.mock('./DynamicFormRenderer', () => ({
  DynamicFormRenderer: () => <div>preview</div>,
}))

const definition: FormDefinition = {
  id: '10000000-0000-0000-0000-000000000001',
  workspace_id: '20000000-0000-0000-0000-000000000001',
  entity_type_id: '30000000-0000-0000-0000-000000000001',
  key: 'service_form',
  name: 'فرم خدمت',
  description: null,
  version_number: 1,
  lifecycle_status: 'DRAFT',
  schema_json: { sections: [] },
  fields: [],
}

describe('FormDesignerPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listForms).mockResolvedValue({ items: [definition], page: 1, page_size: 200, total: 1 })
    vi.mocked(getForm).mockResolvedValue(definition)
    vi.mocked(listEntityTypes).mockResolvedValue({ items: [], page: 1, page_size: 200, total: 0 })
    vi.mocked(listAttributes).mockResolvedValue([])
    vi.mocked(updateFormSections).mockResolvedValue({
      ...definition,
      schema_json: { sections: [{ key: 'general', label: 'عمومی', display_order: 10, configuration: {} }] },
    })
    vi.mocked(publishForm).mockResolvedValue({ ...definition, lifecycle_status: 'PUBLISHED' })
    vi.mocked(createNewFormVersion).mockResolvedValue({
      ...definition,
      id: '10000000-0000-0000-0000-000000000002',
      version_number: 2,
    })
  })

  it('adds a metadata-defined section to a draft form', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${definition.workspace_id}/forms`]}>
        <Routes>
          <Route path="/workspaces/:workspaceId/forms" element={<FormDesignerPage />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'طراحی' }))
    const sectionForm = screen.getByRole('form', { name: 'افزودن بخش' })
    await user.type(within(sectionForm).getByLabelText(/کلید پایدار/), 'general')
    await user.type(within(sectionForm).getByLabelText(/برچسب نمایشی/), 'عمومی')
    await user.clear(within(sectionForm).getByLabelText(/ترتیب نمایش/))
    await user.type(within(sectionForm).getByLabelText(/ترتیب نمایش/), '10')
    await user.click(within(sectionForm).getByRole('button', { name: 'افزودن بخش' }))

    expect(updateFormSections).toHaveBeenCalledWith(definition.id, [{
      key: 'general',
      label: 'عمومی',
      display_order: 10,
      configuration: {},
    }])
  })

  it('requires confirmation before publishing an immutable version', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${definition.workspace_id}/forms`]}>
        <Routes><Route path="/workspaces/:workspaceId/forms" element={<FormDesignerPage />} /></Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'طراحی' }))
    await user.click(await screen.findByRole('button', { name: 'انتشار فرم' }))
    expect(publishForm).not.toHaveBeenCalled()
    const dialog = screen.getByRole('dialog', { name: 'انتشار نسخه فرم؟' })
    await user.click(within(dialog).getByRole('button', { name: 'انتشار فرم' }))

    expect(publishForm).toHaveBeenCalledWith(definition.id)
  })

  it('copies a published version into a new selected draft', async () => {
    vi.mocked(listForms).mockResolvedValue({
      items: [{ ...definition, lifecycle_status: 'PUBLISHED' }],
      page: 1,
      page_size: 200,
      total: 1,
    })
    const user = userEvent.setup()
    renderWithProviders(
      <MemoryRouter initialEntries={[`/workspaces/${definition.workspace_id}/forms`]}>
        <Routes><Route path="/workspaces/:workspaceId/forms" element={<FormDesignerPage />} /></Routes>
      </MemoryRouter>,
    )

    await user.click(await screen.findByRole('button', { name: 'ایجاد نسخه جدید' }))

    expect(createNewFormVersion).toHaveBeenCalledWith(definition.id)
    await waitFor(() => expect(getForm).toHaveBeenCalledWith('10000000-0000-0000-0000-000000000002'))
  })
})
