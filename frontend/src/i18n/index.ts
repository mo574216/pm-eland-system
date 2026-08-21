import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import { fa } from './fa'

document.documentElement.lang = 'fa'
document.documentElement.dir = 'rtl'

void i18n.use(initReactI18next).init({
  fallbackLng: 'fa',
  interpolation: { escapeValue: false },
  lng: 'fa',
  resources: { fa: { translation: fa } },
  supportedLngs: ['fa'],
})

export { i18n }
