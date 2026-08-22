import { CacheProvider } from '@emotion/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { CssBaseline, ThemeProvider } from '@mui/material'
import type { PropsWithChildren } from 'react'
import { I18nextProvider } from 'react-i18next'
import { Provider as ReduxProvider } from 'react-redux'

import { i18n } from '../i18n'
import { AuthProvider } from '../modules/auth/AuthProvider'
import { store } from '../store/store'
import { queryClient } from './queryClient'
import { rtlCache } from './rtlCache'
import { theme } from './theme'

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <I18nextProvider i18n={i18n}>
      <CacheProvider value={rtlCache}>
        <ReduxProvider store={store}>
          <AuthProvider>
            <QueryClientProvider client={queryClient}>
              <ThemeProvider theme={theme}>
                <CssBaseline />
                {children}
              </ThemeProvider>
            </QueryClientProvider>
          </AuthProvider>
        </ReduxProvider>
      </CacheProvider>
    </I18nextProvider>
  )
}
