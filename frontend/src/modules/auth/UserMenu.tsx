import { AccountCircleOutlined } from '@mui/icons-material'
import { Alert, IconButton, Menu, MenuItem, Stack, Typography } from '@mui/material'
import { useState, type MouseEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

import { useAuth } from './authContext'

export function UserMenu() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [anchorElement, setAnchorElement] = useState<HTMLElement | null>(null)
  const [logoutFailed, setLogoutFailed] = useState(false)

  const openMenu = (event: MouseEvent<HTMLElement>) => {
    setAnchorElement(event.currentTarget)
    setLogoutFailed(false)
  }

  const closeMenu = () => setAnchorElement(null)

  const handleLogout = async () => {
    try {
      await logout()
      closeMenu()
      void navigate('/login', { replace: true })
    } catch {
      setLogoutFailed(true)
    }
  }

  return (
    <>
      <IconButton
        aria-controls={anchorElement === null ? undefined : 'user-menu'}
        aria-expanded={anchorElement === null ? undefined : 'true'}
        aria-haspopup="menu"
        aria-label={t('app.userMenu')}
        color="inherit"
        onClick={openMenu}
      >
        <AccountCircleOutlined />
      </IconButton>
      <Menu
        anchorEl={anchorElement}
        id="user-menu"
        onClose={closeMenu}
        open={anchorElement !== null}
      >
        <Stack sx={{ maxWidth: 280, px: 2, py: 1 }}>
          <Typography sx={{ fontWeight: 700 }}>{user?.display_name ?? user?.username}</Typography>
          {logoutFailed ? <Alert severity="error">{t('auth.logoutFailed')}</Alert> : null}
        </Stack>
        <MenuItem onClick={() => void handleLogout()}>{t('auth.logout')}</MenuItem>
      </Menu>
    </>
  )
}
