import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { ApiError } from '../../api/client'
import { renderWithProviders } from '../../test/render'
import { DynamicFormRenderer } from './DynamicFormRenderer'
import { createFormInstance, renderForm, saveFormInstance } from './formApi'
import type { FormInstance, FormRenderContract } from './types'

vi.mock('./formApi', () => ({
  createFormInstance: vi.fn(),
  renderForm: vi.fn(),
  saveFormInstance: vi.fn(),
}))

const contract: FormRenderContract = {
  form: {
    id: '10000000-0000-0000-0000-000000000001',
    key: 'specification',
    name: 'فرم مشخصات',
    version_number: 1,
    lifecycle_status: 'PUBLISHED',
  },
  entity_id: '20000000-0000-0000-0000-000000000001',
  sections: [{
    key: 'general',
    label: 'اطلاعات عمومی',
    order: 10,
    configuration: {},
    fields: [{
      key: 'summary',
      label: 'خلاصه',
      type: 'TEXT',
      required: true,
      read_only: false,
      visible: true,
      value: 'مقدار اولیه',
      has_value: true,
      value_source: 'CURRENT',
      configuration: {},
      visibility_rule: {},
      validation_rule: {},
    }],
  }],
}

const instance: FormInstance = {
  id: '30000000-0000-0000-0000-000000000001',
  workspace_id: '40000000-0000-0000-0000-000000000001',
  form_definition_id: contract.form.id,
  entity_id: contract.entity_id ?? '',
  status: 'DRAFT',
  values: {},
  version: 1,
  created_at: '2026-08-23T00:00:00Z',
  updated_at: '2026-08-23T00:00:00Z',
  submitted_by: null,
  submitted_at: null,
  form: contract.form,
}

describe('DynamicFormRenderer', () => {
  beforeEach(() => {
    vi.mocked(renderForm).mockReset()
    vi.mocked(createFormInstance).mockReset()
    vi.mocked(saveFormInstance).mockReset()
    vi.mocked(renderForm).mockResolvedValue(contract)
    vi.mocked(createFormInstance).mockResolvedValue(instance)
  })

  it('renders sections and creates then saves a versioned draft', async () => {
    vi.mocked(saveFormInstance).mockResolvedValue({
      ...instance,
      values: { summary: 'مقدار اولیه' },
      version: 2,
    })
    const user = userEvent.setup()
    renderWithProviders(
      <DynamicFormRenderer canEdit entityId={contract.entity_id ?? ''} formId={contract.form.id} />,
    )

    expect(await screen.findByRole('heading', { name: 'اطلاعات عمومی' })).toBeVisible()
    expect(screen.getByLabelText(/خلاصه/)).toHaveValue('مقدار اولیه')
    await user.click(screen.getByRole('button', { name: 'ذخیره پیش‌نویس' }))

    expect(createFormInstance).toHaveBeenCalledWith(contract.form.id, contract.entity_id)
    expect(saveFormInstance).toHaveBeenCalledWith(instance.id, { summary: 'مقدار اولیه' }, 1)
    expect(await screen.findByText('پیش‌نویس فرم ذخیره شد.')).toBeVisible()
  })

  it('maps authoritative backend validation details to fields', async () => {
    vi.mocked(saveFormInstance).mockRejectedValue(
      new ApiError(422, 'VALIDATION_ERROR', {
        fields: [{ field: 'summary', code: 'MIN_LENGTH' }],
      }),
    )
    const user = userEvent.setup()
    renderWithProviders(
      <DynamicFormRenderer canEdit entityId={contract.entity_id ?? ''} formId={contract.form.id} />,
    )
    await user.click(await screen.findByRole('button', { name: 'ذخیره پیش‌نویس' }))

    expect(await screen.findByText('طول مقدار کمتر از حد مجاز است.')).toBeVisible()
    expect(screen.getByText('یک یا چند مقدار فرم معتبر نیست.')).toBeVisible()
  })
})
