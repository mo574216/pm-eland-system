import {
  ArrowBackIosNewRounded,
  BusinessCenterOutlined,
  CloseRounded,
  MenuRounded,
  NotificationsNoneRounded,
} from '@mui/icons-material'
import {
  AppBar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Outlet, useLocation, useParams } from 'react-router-dom'

import { UserMenu } from '../modules/auth/UserMenu'
import { getWorkspace } from '../modules/workspaces/workspaceApi'
import { WorkspaceSelector } from '../modules/workspaces/WorkspaceSelector'
import { workspaceNavigation } from './workspaceNavigation'

const drawerWidth = 286

export function AppShell() {
  const { t } = useTranslation()
  const theme = useTheme()
  const location = useLocation()
  const { workspaceId } = useParams()
  const desktop = useMediaQuery(theme.breakpoints.up('lg'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const workspace = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => getWorkspace(workspaceId ?? ''),
    enabled: workspaceId !== undefined,
  })

  const isActive = (path: string) =>
    location.pathname === path ||
    (path.endsWith('/entities') && location.pathname.startsWith(`${path}/`))

  const drawer = (
    <Stack sx={{ height: '100%' }}>
      <Stack direction="row" sx={{ alignItems: 'center', gap: 1.5, minHeight: 82, px: 2.5 }}>
        <Box
          aria-hidden="true"
          sx={{
            alignItems: 'center',
            background: 'linear-gradient(145deg, #1684b6, #6953af)',
            borderRadius: 3,
            color: 'common.white',
            display: 'flex',
            height: 46,
            justifyContent: 'center',
            width: 46,
          }}
        >
          <BusinessCenterOutlined />
        </Box>
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ fontWeight: 900 }} variant="subtitle1">
            {t('app.productShortName')}
          </Typography>
          <Typography color="text.secondary" noWrap variant="caption">
            {t('app.productTagline')}
          </Typography>
        </Box>
        {!desktop ? (
          <IconButton
            aria-label={t('app.closeMenu')}
            onClick={() => setMobileOpen(false)}
            sx={{ mr: 'auto' }}
          >
            <CloseRounded />
          </IconButton>
        ) : null}
      </Stack>
      <Divider />
      {workspaceId ? (
        <>
          <Box sx={{ px: 2.5, py: 2 }}>
            <Typography color="text.secondary" variant="caption">
              {t('app.workspaceContext')}
            </Typography>
            <Typography noWrap sx={{ fontWeight: 800 }}>
              {workspace.data?.name ?? '…'}
            </Typography>
          </Box>
          <Box component="nav" aria-label={t('navigation.primary')}>
            <List sx={{ px: 1.5 }}>
              {workspaceNavigation.map((item) => {
                const path = item.path(workspaceId)
                const Icon = item.icon
                return (
                  <ListItemButton
                    component={Link}
                    key={item.key}
                    onClick={() => setMobileOpen(false)}
                    selected={isActive(path)}
                    sx={{
                      borderRadius: 2.5,
                      mb: 0.5,
                      '&.Mui-selected': { color: 'primary.dark' },
                    }}
                    to={path}
                  >
                    <ListItemIcon sx={{ color: 'inherit', minWidth: 42 }}>
                      <Icon />
                    </ListItemIcon>
                    <ListItemText primary={t(`navigation.${item.key}`)} />
                  </ListItemButton>
                )
              })}
            </List>
          </Box>
        </>
      ) : null}
      <Box sx={{ flexGrow: 1 }} />
      <Divider />
      <List sx={{ p: 1.5 }}>
        <ListItemButton
          component={Link}
          onClick={() => setMobileOpen(false)}
          sx={{ borderRadius: 2.5 }}
          to="/workspaces"
        >
          <ListItemIcon sx={{ minWidth: 42 }}>
            <ArrowBackIosNewRounded fontSize="small" />
          </ListItemIcon>
          <ListItemText primary={t('navigation.workspaces')} />
        </ListItemButton>
      </List>
    </Stack>
  )

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {workspaceId ? (
        <Drawer
          anchor="right"
          ModalProps={{ keepMounted: true }}
          onClose={() => setMobileOpen(false)}
          open={desktop || mobileOpen}
          variant={desktop ? 'permanent' : 'temporary'}
          sx={{
            '& .MuiDrawer-paper': {
              borderLeft: '1px solid',
              borderColor: 'divider',
              width: drawerWidth,
            },
          }}
        >
          {drawer}
        </Drawer>
      ) : null}
      <Box sx={{ minHeight: '100vh', mr: { lg: workspaceId ? `${drawerWidth}px` : 0 } }}>
        <AppBar
          color="inherit"
          elevation={0}
          position="sticky"
          sx={{
            backdropFilter: 'blur(12px)',
            bgcolor: 'rgba(255,255,255,0.94)',
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Toolbar sx={{ gap: 1.5, minHeight: { xs: 72, md: 82 } }}>
            {workspaceId && !desktop ? (
              <IconButton aria-label={t('app.menu')} onClick={() => setMobileOpen(true)}>
                <MenuRounded />
              </IconButton>
            ) : null}
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Typography color="text.secondary" variant="caption">
                {workspaceId ? t('dashboard.title') : t('app.title')}
              </Typography>
              <Typography noWrap sx={{ fontWeight: 900 }} variant="h6">
                {workspace.data?.name ?? t('app.title')}
              </Typography>
            </Box>
            <WorkspaceSelector />
            <Tooltip title={t('dashboard.announcements')}>
              <IconButton aria-label={t('dashboard.announcements')}>
                <NotificationsNoneRounded />
              </IconButton>
            </Tooltip>
            <UserMenu />
          </Toolbar>
        </AppBar>
        <Box
          component="main"
          sx={{
            backgroundImage:
              'radial-gradient(circle at 8% 12%, rgba(113,87,183,.08), transparent 22rem), radial-gradient(circle at 92% 88%, rgba(22,111,155,.08), transparent 26rem)',
            minHeight: 'calc(100vh - 82px)',
            px: { xs: 2, sm: 3, md: 5 },
            py: { xs: 3, md: 4 },
          }}
        >
          <Box sx={{ maxWidth: 1440, mx: 'auto' }}>
            <Outlet />
          </Box>
        </Box>
      </Box>
    </Box>
  )
}
