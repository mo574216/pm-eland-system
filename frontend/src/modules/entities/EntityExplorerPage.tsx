import { Button, Stack, Typography } from '@mui/material'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { EntityTreeViewer } from './EntityTreeViewer'

export function EntityExplorerPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { workspaceId } = useParams()
  const [selectedEntityId, setSelectedEntityId] = useState<string>()

  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />

  return (
    <Stack spacing={3}>
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography component="h1" variant="h1">
          {t('entities.title')}
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button onClick={() => void navigate(`/workspaces/${workspaceId}/metadata`)}>
            {t('entities.metadata')}
          </Button>
          <Button onClick={() => void navigate(`/workspaces/${workspaceId}/settings`)}>
            {t('entities.settings')}
          </Button>
        </Stack>
      </Stack>
      <EntityTreeViewer
        onSelect={setSelectedEntityId}
        selectedEntityId={selectedEntityId}
        workspaceId={workspaceId}
      />
    </Stack>
  )
}
