import type { FormOption } from './types'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

export function normalizeOptions(value: unknown): FormOption[] {
  if (!Array.isArray(value)) return []
  return value.flatMap((option): FormOption[] => {
    if (typeof option === 'string') return [{ value: option, label: option }]
    if (isRecord(option) && typeof option.value === 'string') {
      return [
        {
          value: option.value,
          label: 'label' in option && typeof option.label === 'string' ? option.label : option.value,
        },
      ]
    }
    return []
  })
}
