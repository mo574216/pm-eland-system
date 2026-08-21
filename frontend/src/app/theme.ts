import { faIR } from '@mui/material/locale'
import { createTheme } from '@mui/material/styles'

export const theme = createTheme(
  {
    direction: 'rtl',
    palette: {
      mode: 'light',
      primary: { main: '#1f5f74' },
      secondary: { main: '#9a5b13' },
      background: { default: '#f5f7f8' },
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily: 'Vazirmatn, Tahoma, Arial, sans-serif',
      h1: { fontSize: '2rem', fontWeight: 700 },
    },
  },
  faIR,
)
