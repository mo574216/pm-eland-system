import { AccountCircleOutlined } from '@mui/icons-material'
import { AppBar, Box, Container, IconButton, Toolbar, Typography } from '@mui/material'
import { Outlet } from 'react-router-dom'

export function AppShell() {
  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography component="div" sx={{ flexGrow: 1 }} variant="h6">
            Project Knowledge Platform
          </Typography>
          <IconButton aria-label="User menu" color="inherit">
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
