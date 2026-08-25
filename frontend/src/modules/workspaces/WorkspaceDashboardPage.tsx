import {
  AccountTreeOutlined,
  CampaignOutlined,
  DashboardCustomizeOutlined,
  DescriptionOutlined,
  FileUploadOutlined,
  FormatListNumberedRtlOutlined,
  SettingsOutlined,
  TuneOutlined,
  ViewQuiltOutlined,
} from '@mui/icons-material'
import { Alert, Box, Button, Card, CardContent, Chip, Grid, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { DashboardKpis } from '../dashboard/DashboardKpis'

interface CapabilityCardProps {
  title: string
  description?: string
  icon: ReactNode
  onOpen?: () => void
}

function CapabilityCard({ title, description, icon, onOpen }: CapabilityCardProps) {
  const { t } = useTranslation()
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack spacing={2} sx={{ height: '100%' }}>
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ alignItems: 'center', bgcolor: onOpen ? 'primary.light' : 'grey.100', borderRadius: 3, color: onOpen ? 'primary.dark' : 'text.secondary', display: 'flex', height: 48, justifyContent: 'center', width: 48 }}>
              {icon}
            </Box>
            <Chip color={onOpen ? 'success' : 'default'} label={t(onOpen ? 'dashboard.available' : 'dashboard.planned')} size="small" variant={onOpen ? 'filled' : 'outlined'} />
          </Stack>
          <Box sx={{ flexGrow: 1 }}>
            <Typography component="h3" variant="h6">{title}</Typography>
            {description ? <Typography color="text.secondary" sx={{ mt: 0.75 }} variant="body2">{description}</Typography> : null}
          </Box>
          {onOpen ? <Button onClick={onOpen} sx={{ alignSelf: 'flex-start' }}>{t('dashboard.open')}</Button> : null}
        </Stack>
      </CardContent>
    </Card>
  )
}

export function WorkspaceDashboardPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { workspaceId } = useParams()
  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />

  const available = [
    { title: t('navigation.phases'), description: t('dashboard.phasesDescription'), icon: <FormatListNumberedRtlOutlined />, path: `/workspaces/${workspaceId}/phases` },
    { title: t('navigation.entities'), description: t('dashboard.entitiesDescription'), icon: <AccountTreeOutlined />, path: `/workspaces/${workspaceId}/entities` },
    { title: t('navigation.metadata'), description: t('dashboard.metadataDescription'), icon: <TuneOutlined />, path: `/workspaces/${workspaceId}/metadata` },
    { title: t('dashboard.forms'), description: t('dashboard.formsDescription'), icon: <ViewQuiltOutlined />, path: `/workspaces/${workspaceId}/forms` },
    { title: t('dashboard.imports'), description: t('dashboard.importsDescription'), icon: <FileUploadOutlined />, path: `/workspaces/${workspaceId}/imports` },
    { title: t('navigation.settings'), description: t('dashboard.settingsDescription'), icon: <SettingsOutlined />, path: `/workspaces/${workspaceId}/settings` },
  ]
  const planned = [
    { title: t('dashboard.documents'), icon: <DescriptionOutlined /> },
    { title: t('dashboard.reports'), icon: <DashboardCustomizeOutlined /> },
  ]

  return (
    <Stack spacing={4}>
      <Box>
        <Typography component="h1" variant="h1">{t('dashboard.welcome')}</Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>{t('dashboard.description')}</Typography>
      </Box>
      <Box component="section" aria-label={t('dashboard.kpiSection')}>
        <DashboardKpis workspaceId={workspaceId} />
      </Box>
      <Box component="section" aria-labelledby="quick-access-title">
        <Typography component="h2" id="quick-access-title" sx={{ mb: 2 }} variant="h2">{t('dashboard.quickAccess')}</Typography>
        <Grid container spacing={2}>
          {available.map((item) => (
            <Grid key={item.path} size={{ xs: 12, md: 6, xl: 4 }}>
              <CapabilityCard description={item.description} icon={item.icon} onOpen={() => void navigate(item.path)} title={item.title} />
            </Grid>
          ))}
          {planned.map((item) => (
            <Grid key={item.title} size={{ xs: 12, sm: 6, xl: 3 }}>
              <CapabilityCard icon={item.icon} title={item.title} />
            </Grid>
          ))}
        </Grid>
      </Box>
      <Card component="section" aria-labelledby="announcements-title">
        <CardContent>
          <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
            <CampaignOutlined color="secondary" />
            <Typography component="h2" id="announcements-title" variant="h2">{t('dashboard.announcements')}</Typography>
          </Stack>
          <Alert icon={<CampaignOutlined />} severity="info" sx={{ bgcolor: 'secondary.light', color: 'secondary.dark' }}>
            <Typography sx={{ fontWeight: 800 }}>{t('dashboard.announcementsEmpty')}</Typography>
            <Typography variant="body2">{t('dashboard.announcementsHint')}</Typography>
          </Alert>
        </CardContent>
      </Card>
    </Stack>
  )
}
