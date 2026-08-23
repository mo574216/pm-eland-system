import { Alert, Button, CircularProgress, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { DynamicFormRenderer } from './DynamicFormRenderer'
import { listPublishedForms } from './formApi'

interface EntityFormsPanelProps {
  workspaceId: string
  entityId: string
  entityTypeId: string
  canEdit: boolean
}

export function EntityFormsPanel({ workspaceId, entityId, entityTypeId, canEdit }: EntityFormsPanelProps) {
  const { t } = useTranslation()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const forms = useQuery({
    queryKey: ['published-forms', workspaceId, entityTypeId],
    queryFn: () => listPublishedForms(workspaceId, entityTypeId),
  })
  if (forms.isPending) return <CircularProgress aria-label={t('forms.loadingList')} />
  if (forms.isError) return <Alert severity="error">{t('forms.listLoadFailed')}</Alert>
  if (forms.data.items.length === 0) return <Alert severity="info">{t('forms.empty')}</Alert>
  const activeId = selectedId ?? forms.data.items[0].id

  return (
    <Stack spacing={3}>
      <Typography component="h2" variant="h2">{t('entities.tabs.forms')}</Typography>
      <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
        {forms.data.items.map((form) => (
          <Button key={form.id} onClick={() => setSelectedId(form.id)} variant={form.id === activeId ? 'contained' : 'outlined'}>
            {form.name}
          </Button>
        ))}
      </Stack>
      <DynamicFormRenderer canEdit={canEdit} entityId={entityId} formId={activeId} key={activeId} />
    </Stack>
  )
}
