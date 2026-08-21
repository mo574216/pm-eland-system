import createCache from '@emotion/cache'
import rtlPlugin from '@mui/stylis-plugin-rtl'
import { prefixer } from 'stylis'

export const rtlCache = createCache({
  key: 'mui-rtl',
  stylisPlugins: [prefixer, rtlPlugin],
})
