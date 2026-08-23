import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { renderWithProviders } from '../../test/render'
import { DynamicFieldRenderer } from './DynamicFieldRenderer'
import type { FormRenderField } from './types'

function field(values: Partial<FormRenderField> = {}): FormRenderField {
  return {
    key: 'summary',
    label: 'خلاصه',
    type: 'TEXT',
    required: true,
    read_only: false,
    visible: true,
    value: null,
    has_value: false,
    value_source: 'NONE',
    configuration: {},
    visibility_rule: {},
    validation_rule: {},
    ...values,
  }
}

describe('DynamicFieldRenderer', () => {
  it('renders visible scalar metadata and preserves inherited read-only state', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const { rerender } = renderWithProviders(
      <DynamicFieldRenderer field={field()} onChange={onChange} value="" />,
    )
    await user.type(screen.getByLabelText(/خلاصه/), 'شرح نمونه')
    expect(onChange).toHaveBeenCalled()

    rerender(
      <DynamicFieldRenderer
        field={field({ read_only: true, value_source: 'INHERITED' })}
        onChange={onChange}
        value="مقدار والد"
      />,
    )
    expect(screen.getByLabelText(/خلاصه/)).toBeDisabled()
    expect(screen.getByText('مقدار به‌ارث‌رسیده')).toBeVisible()

    rerender(
      <DynamicFieldRenderer field={field({ visible: false })} onChange={onChange} value="" />,
    )
    expect(screen.queryByLabelText(/خلاصه/)).not.toBeInTheDocument()
  })

  it('adds, edits, and removes metadata-defined repeating rows', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const table = field({
      key: 'risks',
      label: 'ریسک‌ها',
      type: 'TABLE',
      required: false,
      configuration: {
        columns: [{ key: 'title', label: 'عنوان', type: 'TEXT', required: true }],
      },
    })
    const { rerender } = renderWithProviders(
      <DynamicFieldRenderer field={table} onChange={onChange} value={[]} />,
    )
    await user.click(screen.getByRole('button', { name: 'افزودن ردیف' }))
    expect(onChange).toHaveBeenLastCalledWith([{ title: null }])

    rerender(
      <DynamicFieldRenderer field={table} onChange={onChange} value={[{ title: null }]} />,
    )
    await user.type(screen.getByLabelText(/عنوان/), 'ریسک نمونه')
    expect(onChange).toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'حذف ردیف' }))
    expect(onChange).toHaveBeenLastCalledWith([])
  })
})
