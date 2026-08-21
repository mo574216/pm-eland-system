import { CacheProvider } from '@emotion/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { render, type RenderOptions } from '@testing-library/react'
import type { PropsWithChildren, ReactElement } from 'react'
import { I18nextProvider } from 'react-i18next'
import { Provider as ReduxProvider } from 'react-redux'

import { rtlCache } from '../app/rtlCache'
import { theme } from '../app/theme'
import { i18n } from '../i18n'
import { store } from '../store/store'

export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

  function Wrapper({ children }: PropsWithChildren) {
    return (
      <I18nextProvider i18n={i18n}>
        <CacheProvider value={rtlCache}>
          <ReduxProvider store={store}>
            <QueryClientProvider client={queryClient}>
              <ThemeProvider theme={theme}>
                <CssBaseline />
                {children}
              </ThemeProvider>
            </QueryClientProvider>
          </ReduxProvider>
        </CacheProvider>
      </I18nextProvider>
    )
  }

  return render(ui, { wrapper: Wrapper, ...options })
}
