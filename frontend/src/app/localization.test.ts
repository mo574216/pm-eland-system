import { theme } from './theme'
import { i18n } from '../i18n'

describe('Persian localization foundation', () => {
  it('configures the document and Material UI for Persian RTL rendering', () => {
    expect(document.documentElement).toHaveAttribute('lang', 'fa')
    expect(document.documentElement).toHaveAttribute('dir', 'rtl')
    expect(theme.direction).toBe('rtl')
    expect(i18n.language).toBe('fa')
  })
})
