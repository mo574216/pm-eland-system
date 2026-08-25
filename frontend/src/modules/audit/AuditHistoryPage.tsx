import { HistoryOutlined, PersonOutlineRounded } from '@mui/icons-material'
import { Alert, Box, Card, CardContent, Chip, CircularProgress, Pagination, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import { getAuditHistory } from './auditApi'

const actionLabels: Record<string, string> = {
  CREATED: 'ایجاد شد',
  UPDATED: 'ویرایش شد',
  DELETED: 'حذف شد',
  ARCHIVED: 'بایگانی شد',
  LOCKED: 'قفل شد',
  UNLOCKED: 'از قفل خارج شد',
  PUBLISHED: 'منتشر شد',
  UPLOADED: 'بارگذاری شد',
}

function friendlyAction(action: string): string {
  const suffix = Object.keys(actionLabels).find((value) => action.endsWith(value))
  return suffix === undefined ? action.replaceAll('_', ' ') : actionLabels[suffix]
}

export function AuditHistoryPage() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const [page, setPage] = useState(1)
  const history = useQuery({
    queryKey: ['audit-history', workspaceId, page],
    queryFn: () => getAuditHistory(workspaceId ?? '', page),
    enabled: workspaceId !== undefined,
  })
  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />

  return (
    <Stack spacing={3}>
      <Box>
        <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
          <HistoryOutlined color="primary" />
          <Typography component="h1" variant="h1">{t('audit.title')}</Typography>
        </Stack>
        <Typography color="text.secondary" sx={{ mt: 1 }}>{t('audit.description')}</Typography>
      </Box>
      {history.isPending ? <CircularProgress aria-label={t('audit.loading')} /> : null}
      {history.isError ? <Alert severity="error">{t('audit.loadFailed')}</Alert> : null}
      {history.data?.items.length === 0 ? <Alert severity="info">{t('audit.empty')}</Alert> : null}
      <Stack spacing={1.5}>
        {history.data?.items.map((entry) => (
          <Card key={entry.id} variant="outlined">
            <CardContent>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ alignItems: { sm: 'center' } }}>
                <Box sx={{ flexGrow: 1 }}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 0.75 }}>
                    <Chip color="primary" label={friendlyAction(entry.action)} size="small" variant="outlined" />
                    <Typography sx={{ fontWeight: 800 }}>{entry.resource_type}</Typography>
                  </Stack>
                  <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center' }}>
                    <PersonOutlineRounded color="action" fontSize="small" />
                    <Typography color="text.secondary" variant="body2">{entry.actor_name}</Typography>
                  </Stack>
                </Box>
                <Typography color="text.secondary" component="time" dateTime={entry.created_at} variant="body2">
                  {new Intl.DateTimeFormat('fa-IR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(entry.created_at))}
                </Typography>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>
      {history.data && history.data.total > history.data.page_size ? (
        <Pagination
          count={Math.ceil(history.data.total / history.data.page_size)}
          onChange={(_, value) => setPage(value)}
          page={page}
          sx={{ alignSelf: 'center', direction: 'ltr' }}
        />
      ) : null}
    </Stack>
  )
}
