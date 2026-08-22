import { CircularProgress, Stack } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './authContext'

export function ProtectedRoute() {
  const { t } = useTranslation()
  const location = useLocation()
  const { status } = useAuth()

  if (status === 'initializing') {
    return (
      <Stack sx={{ alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <CircularProgress aria-label={t('auth.restoringSession')} />
      </Stack>
    )
  }

  if (status === 'anonymous') {
    return <Navigate replace state={{ from: location }} to="/login" />
  }

  return <Outlet />
}
