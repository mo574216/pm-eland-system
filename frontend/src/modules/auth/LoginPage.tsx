import { Button, Paper, Stack, TextField, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

export function LoginPage() {
  const { t } = useTranslation()

  return (
    <Stack sx={{ alignItems: 'center', justifyContent: 'center', minHeight: '100vh', p: 2 }}>
      <Paper component="main" elevation={2} sx={{ maxWidth: 420, p: 4, width: '100%' }}>
        <Stack component="form" spacing={3}>
          <Typography component="h1" variant="h1">
            {t('auth.signIn')}
          </Typography>
          <TextField
            autoComplete="username"
            label={t('auth.email')}
            name="email"
            required
            type="email"
          />
          <TextField
            autoComplete="current-password"
            label={t('auth.password')}
            name="password"
            required
            type="password"
          />
          <Button disabled type="submit" variant="contained">
            {t('auth.signIn')}
          </Button>
          <Typography color="text.secondary" variant="body2">
            {t('auth.pending')}
          </Typography>
        </Stack>
      </Paper>
    </Stack>
  )
}
