import { faIR } from '@mui/material/locale'
import { createTheme } from '@mui/material/styles'

export const theme = createTheme(
  {
    direction: 'rtl',
    palette: {
      mode: 'light',
      primary: { main: '#166f9b', dark: '#0d4f74', light: '#e4f4fb' },
      secondary: { main: '#7157b7', dark: '#4e3b85', light: '#eeeafb' },
      background: { default: '#f7f9fb', paper: '#ffffff' },
    },
    shape: { borderRadius: 14 },
    typography: {
      fontFamily: 'Vazirmatn, Tahoma, Arial, sans-serif',
      h1: { fontSize: '2rem', fontWeight: 700 },
      h2: { fontSize: '1.35rem', fontWeight: 800 },
      button: { fontWeight: 700 },
    },
    components: {
      MuiButton: { defaultProps: { disableElevation: true } },
      MuiCard: {
        styleOverrides: {
          root: { border: '1px solid #e4eaf0', boxShadow: '0 10px 30px rgba(24, 62, 83, 0.07)' },
        },
      },
      MuiCssBaseline: {
        styleOverrides: {
          body: { backgroundColor: '#f7f9fb' },
          '*:focus-visible': { outline: '3px solid rgba(22, 111, 155, 0.35)', outlineOffset: 2 },
        },
      },
    },
  },
  faIR,
)
