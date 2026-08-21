import { Button, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  const { t } = useTranslation()

  return (
    <Stack component="main" spacing={2} sx={{ alignItems: 'center', p: 6 }}>
      <Typography component="h1" variant="h1">
        {t('notFound.title')}
      </Typography>
      <Button component={Link} to="/workspaces" variant="contained">
        {t('notFound.returnToWorkspaces')}
      </Button>
    </Stack>
  )
}
