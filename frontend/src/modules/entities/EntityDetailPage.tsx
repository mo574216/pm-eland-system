import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { listAttributes } from '../metadata/metadataApi'
import { EntityFormsPanel } from '../forms/EntityFormsPanel'
import { RelationshipPanel } from '../relationships/RelationshipPanel'
import type { RootState } from '../../store/store'
import { getEntity } from './entityApi'

const tabKeys = ['overview', 'information', 'forms', 'documents', 'relationships', 'history'] as const
type TabKey = (typeof tabKeys)[number]

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? '✓' : '✕'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'bigint') return value.toString()
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return '—'
}

export function EntityDetailPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const canManageRelationships = useSelector((state: RootState) =>
    state.auth.user?.permissions.includes('RELATIONSHIP_MANAGE'),
  ) ?? false
  const canSubmitForms = useSelector((state: RootState) =>
    state.auth.user?.permissions.includes('FORM_SUBMIT'),
  ) ?? false
  const { workspaceId, entityId } = useParams()
  const [activeTab, setActiveTab] = useState<TabKey>('overview')
  const entity = useQuery({
    queryKey: ['entity', entityId],
    queryFn: () => getEntity(entityId ?? ''),
    enabled: entityId !== undefined,
  })
  const attributes = useQuery({
    queryKey: ['attributes', entity.data?.entity_type_id],
    queryFn: () => listAttributes(entity.data?.entity_type_id ?? ''),
    enabled: entity.data !== undefined,
  })

  if (workspaceId === undefined || entityId === undefined) {
    return <Navigate replace to="/workspaces" />
  }
  if (entity.isPending) return <CircularProgress aria-label={t('entities.loadingDetail')} />
  if (entity.isError) {
    return (
      <Alert
        action={<Button onClick={() => void entity.refetch()}>{t('entities.retry')}</Button>}
        severity="error"
      >
        {t('entities.detailLoadFailed')}
      </Alert>
    )
  }

  const knownKeys = new Set(attributes.data?.map((definition) => definition.key) ?? [])
  const unknownEntries = attributes.data
    ? Object.entries(entity.data.attributes).filter(([key]) => !knownKeys.has(key))
    : []

  return (
    <Stack spacing={3}>
      <Stack direction="row" sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box>
          <Typography component="h1" variant="h1">
            {entity.data.name}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mt: 1 }}>
            <Chip label={entity.data.entity_type.name} size="small" />
            <Chip label={t(`entities.status.${entity.data.status}`)} size="small" variant="outlined" />
          </Stack>
        </Box>
        <Button onClick={() => void navigate(`/workspaces/${workspaceId}/entities`)}>
          {t('entities.backToTree')}
        </Button>
      </Stack>

      <Tabs
        aria-label={t('entities.detailTabs')}
        onChange={(_, value: TabKey) => setActiveTab(value)}
        scrollButtons="auto"
        value={activeTab}
        variant="scrollable"
      >
        {tabKeys.map((key) => (
          <Tab key={key} label={t(`entities.tabs.${key}`)} value={key} />
        ))}
      </Tabs>
      <Divider />

      {activeTab === 'overview' ? (
        <Stack spacing={2}>
          <Typography component="h2" variant="h5">{t('entities.tabs.overview')}</Typography>
          <Typography>{entity.data.description ?? t('entities.noDescription')}</Typography>
          <Typography color="text.secondary">
            {t('entities.parent')}: {entity.data.parent_id ?? t('entities.rootEntity')}
          </Typography>
          <Typography color="text.secondary">
            {t('entities.version')}: {entity.data.version}
          </Typography>
        </Stack>
      ) : null}

      {activeTab === 'information' ? (
        <Stack spacing={2}>
          <Typography component="h2" variant="h5">{t('entities.tabs.information')}</Typography>
          {attributes.isPending ? <CircularProgress aria-label={t('entities.loadingAttributes')} /> : null}
          {attributes.isError ? <Alert severity="error">{t('entities.attributesLoadFailed')}</Alert> : null}
          {attributes.data?.map((definition) => (
            <Box key={definition.id}>
              <Typography color="text.secondary" variant="caption">{definition.label}</Typography>
              <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap' }}>
                {displayValue(entity.data.attributes[definition.key])}
              </Typography>
            </Box>
          ))}
          {unknownEntries.map(([key, value]) => (
            <Box key={key}>
              <Typography color="text.secondary" dir="ltr" variant="caption">{key}</Typography>
              <Typography component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap' }}>
                {displayValue(value)}
              </Typography>
            </Box>
          ))}
          {attributes.data?.length === 0 && unknownEntries.length === 0 ? (
            <Alert severity="info">{t('entities.noAttributes')}</Alert>
          ) : null}
        </Stack>
      ) : null}

      {activeTab === 'relationships' ? (
        <RelationshipPanel
          canManage={canManageRelationships}
          entityId={entityId}
          workspaceId={workspaceId}
        />
      ) : null}

      {activeTab === 'forms' ? (
        <EntityFormsPanel
          canEdit={canSubmitForms}
          entityId={entityId}
          entityTypeId={entity.data.entity_type_id}
          workspaceId={workspaceId}
        />
      ) : null}

      {!['overview', 'information', 'forms', 'relationships'].includes(activeTab) ? (
        <Alert severity="info">{t('entities.sectionPending')}</Alert>
      ) : null}
    </Stack>
  )
}
