import { AssignmentTurnedInOutlined, DescriptionOutlined, DonutLargeOutlined, HubOutlined } from '@mui/icons-material'
import { Alert, Card, CardContent, CircularProgress, Grid, LinearProgress, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'

import { getDashboardSummary } from './dashboardApi'

export function DashboardKpis({ workspaceId }: { workspaceId: string }) {
  const { t } = useTranslation()
  const summary = useQuery({
    queryKey: ['dashboard-summary', workspaceId],
    queryFn: () => getDashboardSummary(workspaceId),
  })
  if (summary.isPending) return <CircularProgress aria-label={t('dashboard.loadingKpis')} />
  if (summary.isError) return <Alert severity="error">{t('dashboard.kpisLoadFailed')}</Alert>
  const items = [
    { key: 'entities', icon: <HubOutlined color="primary" />, value: summary.data.entity_count },
    { key: 'documents', icon: <DescriptionOutlined color="primary" />, value: summary.data.document_count },
    { key: 'pendingDeliverables', icon: <AssignmentTurnedInOutlined color="warning" />, value: summary.data.deliverables.pending },
  ]
  return (
    <Grid container spacing={2}>
      {items.map((item) => (
        <Grid key={item.key} size={{ xs: 12, sm: 4 }}>
          <Card variant="outlined"><CardContent><Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>{item.icon}<Stack><Typography color="text.secondary">{t(`dashboard.kpi.${item.key}`)}</Typography><Typography variant="h4">{item.value.toLocaleString('fa-IR')}</Typography></Stack></Stack></CardContent></Card>
        </Grid>
      ))}
      <Grid size={{ xs: 12 }}>
        <Card variant="outlined"><CardContent><Stack spacing={1}>
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}><Stack direction="row" spacing={1}><DonutLargeOutlined color="secondary" /><Typography>{t('dashboard.kpi.phaseProgress')}</Typography></Stack><Typography sx={{ fontWeight: 800 }}>{summary.data.phases.percent.toLocaleString('fa-IR')}٪</Typography></Stack>
          <LinearProgress aria-label={t('dashboard.kpi.phaseProgress')} value={summary.data.phases.percent} variant="determinate" />
          <Typography color="text.secondary" variant="body2">
            {t('dashboard.kpi.phaseCount', {
              completed: summary.data.phases.completed.toLocaleString('fa-IR'),
              total: summary.data.phases.total.toLocaleString('fa-IR'),
            })}
          </Typography>
        </Stack></CardContent></Card>
      </Grid>
    </Grid>
  )
}
