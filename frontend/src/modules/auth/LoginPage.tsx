import { Alert, Button, CircularProgress, Paper, Stack, TextField, Typography } from '@mui/material'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { ApiError } from '../../api/client'
import { useAuth } from './authContext'
import type { LoginCredentials } from './types'

const loginSchema = z.object({
  username: z.string().trim().min(1),
  password: z.string().min(1),
})

interface LoginLocationState {
  from?: { pathname?: string }
}

export function LoginPage() {
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()
  const { status, login } = useAuth()
  const [submissionError, setSubmissionError] = useState<string | null>(null)
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    setError,
  } = useForm<LoginCredentials>()

  const state = location.state as LoginLocationState | null
  const destination = state?.from?.pathname ?? '/workspaces'

  if (status === 'authenticated') {
    return <Navigate replace to={destination} />
  }

  const submit = handleSubmit(async (values) => {
    setSubmissionError(null)
    const parsed = loginSchema.safeParse(values)
    if (!parsed.success) {
      if (!values.username.trim()) {
        setError('username', { message: t('auth.usernameRequired') })
      }
      if (!values.password) {
        setError('password', { message: t('auth.passwordRequired') })
      }
      return
    }

    try {
      await login(parsed.data)
      void navigate(destination, { replace: true })
    } catch (error) {
      setSubmissionError(
        error instanceof ApiError && error.code === 'AUTH_INVALID_CREDENTIALS'
          ? t('auth.invalidCredentials')
          : t('auth.loginFailed'),
      )
    }
  })

  return (
    <Stack sx={{ alignItems: 'center', justifyContent: 'center', minHeight: '100vh', p: 2 }}>
      <Paper component="main" elevation={2} sx={{ maxWidth: 420, p: 4, width: '100%' }}>
        <Stack component="form" noValidate onSubmit={(event) => void submit(event)} spacing={3}>
          <Typography component="h1" variant="h1">
            {t('auth.signIn')}
          </Typography>
          {submissionError === null ? null : <Alert severity="error">{submissionError}</Alert>}
          <TextField
            autoComplete="username"
            error={errors.username !== undefined}
            helperText={errors.username?.message}
            label={t('auth.username')}
            required
            {...register('username')}
          />
          <TextField
            autoComplete="current-password"
            error={errors.password !== undefined}
            helperText={errors.password?.message}
            label={t('auth.password')}
            required
            type="password"
            {...register('password')}
          />
          <Button disabled={isSubmitting || status === 'initializing'} type="submit" variant="contained">
            {isSubmitting ? <CircularProgress aria-label={t('auth.signingIn')} size={24} /> : t('auth.signIn')}
          </Button>
        </Stack>
      </Paper>
    </Stack>
  )
}
