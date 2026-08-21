import { Alert, Stack, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

export function WorkspaceListPage() {
  const { t } = useTranslation()

  return (
    <Stack spacing={2}>
      <Typography component="h1" variant="h1">
        {t('workspaces.title')}
      </Typography>
      <Alert severity="info">{t('workspaces.empty')}</Alert>
    </Stack>
  )
}
