import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { renderWithProviders } from '../../test/render'
import { listAttributes, listEntityTypes } from '../metadata/metadataApi'
import { FormDesignerPage } from './FormDesignerPage'
import { getForm, listForms, updateFormSections } from './formApi'
import type { FormDefinition } from './types'

vi.mock('../metadata/metadataApi', () => ({
  listAttributes: vi.fn(),
  listEntityTypes: vi.fn(),
}))

vi.mock('./formApi', () => ({
  addFormField: vi.fn(),
  createForm: vi.fn(),
  getForm: vi.fn(),
  listForms: vi.fn(),
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
    vi.mocked(listForms).mockResolvedValue({ items: [definition], page: 1, page_size: 200, total: 1 })
    vi.mocked(getForm).mockResolvedValue(definition)
    vi.mocked(listEntityTypes).mockResolvedValue({ items: [], page: 1, page_size: 200, total: 0 })
    vi.mocked(listAttributes).mockResolvedValue([])
    vi.mocked(updateFormSections).mockResolvedValue({
      ...definition,
      schema_json: { sections: [{ key: 'general', label: 'عمومی', display_order: 10, configuration: {} }] },
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
})
