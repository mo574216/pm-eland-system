import { Alert, Button, Card, CardActions, CardContent, CircularProgress, Stack, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import type { AppDispatch } from '../../store/store'
import { workspaceSelected } from '../../store/store'
import { listWorkspaces } from './workspaceApi'

export function WorkspaceListPage() {
  const { t } = useTranslation()
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const workspaces = useQuery({ queryKey: ['workspaces'], queryFn: listWorkspaces })

  const openWorkspace = (workspaceId: string) => {
    dispatch(workspaceSelected(workspaceId))
    void navigate(`/workspaces/${workspaceId}/entities`)
  }

  return (
    <Stack spacing={2}>
      <Typography component="h1" variant="h1">
        {t('workspaces.title')}
      </Typography>
      {workspaces.isPending ? (
        <CircularProgress aria-label={t('workspaces.loading')} />
      ) : null}
      {workspaces.isError ? <Alert severity="error">{t('workspaces.loadFailed')}</Alert> : null}
      {workspaces.data?.items.length === 0 ? (
        <Alert severity="info">{t('workspaces.empty')}</Alert>
      ) : null}
      {workspaces.data?.items.map((workspace) => (
        <Card key={workspace.id} variant="outlined">
          <CardContent>
            <Typography component="h2" variant="h5">
              {workspace.name}
            </Typography>
            {workspace.description ? (
              <Typography color="text.secondary">{workspace.description}</Typography>
            ) : null}
          </CardContent>
          <CardActions>
            <Button onClick={() => openWorkspace(workspace.id)}>{t('workspaces.open')}</Button>
          </CardActions>
        </Card>
      ))}
    </Stack>
  )
}
