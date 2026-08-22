import { AppBar, Box, Container, Toolbar, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router-dom'

import { UserMenu } from '../modules/auth/UserMenu'
import { WorkspaceSelector } from '../modules/workspaces/WorkspaceSelector'

export function AppShell() {
  const { t } = useTranslation()

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography component="div" sx={{ flexGrow: 1 }} variant="h6">
            {t('app.title')}
          </Typography>
          <WorkspaceSelector />
          <UserMenu />
        </Toolbar>
      </AppBar>
      <Container component="main" maxWidth="lg" sx={{ py: 4 }}>
        <Outlet />
      </Container>
    </Box>
  )
}
