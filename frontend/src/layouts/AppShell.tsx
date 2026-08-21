import { AccountCircleOutlined } from '@mui/icons-material'
import { AppBar, Box, Container, IconButton, Toolbar, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router-dom'

export function AppShell() {
  const { t } = useTranslation()

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography component="div" sx={{ flexGrow: 1 }} variant="h6">
            {t('app.title')}
          </Typography>
          <IconButton aria-label={t('app.userMenu')} color="inherit">
            <AccountCircleOutlined />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Container component="main" maxWidth="lg" sx={{ py: 4 }}>
        <Outlet />
      </Container>
    </Box>
  )
}
