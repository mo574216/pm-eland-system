import { Alert, Button, CircularProgress, Divider, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { WorkspaceMemberManager } from './WorkspaceMemberManager'
import { getWorkspace, updateWorkspace } from './workspaceApi'

interface WorkspaceSettingsValues {
  name: string
  description: string
}

export function WorkspaceSettingsPage() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const workspace = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => getWorkspace(workspaceId ?? ''),
    enabled: workspaceId !== undefined,
  })
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<WorkspaceSettingsValues>()
  const update = useMutation({
    mutationFn: (values: WorkspaceSettingsValues) =>
      updateWorkspace(workspaceId ?? '', {
        name: values.name.trim(),
        description: values.description.trim() || null,
        version: workspace.data?.version ?? 0,
      }),
    onSuccess: async (updated) => {
      queryClient.setQueryData(['workspace', workspaceId], updated)
      await queryClient.invalidateQueries({ queryKey: ['workspaces'] })
      setSaved(true)
    },
  })

  useEffect(() => {
    if (workspace.data) {
      reset({
        name: workspace.data.name,
        description: workspace.data.description ?? '',
      })
    }
  }, [reset, workspace.data])

  if (workspaceId === undefined) {
    return <Navigate replace to="/workspaces" />
  }

  if (workspace.isPending) {
    return <CircularProgress aria-label={t('workspaces.loading')} />
  }

  if (workspace.isError) {
    return <Alert severity="error">{t('workspaces.loadFailed')}</Alert>
  }

  const submit = handleSubmit(async (values) => {
    setSaveError(null)
    setSaved(false)
    try {
      await update.mutateAsync(values)
    } catch (error) {
      setSaveError(
        error instanceof ApiError && error.code === 'STALE_VERSION'
          ? t('workspaces.staleVersion')
          : t('workspaces.saveFailed'),
      )
    }
  })

  return (
    <Stack spacing={4}>
      <Typography component="h1" variant="h1">
        {t('workspaces.settings')}
      </Typography>
      <Button onClick={() => void navigate(`/workspaces/${workspaceId}/metadata`)}>
        {t('metadata.openAdministration')}
      </Button>
      <Stack component="form" noValidate onSubmit={(event) => void submit(event)} spacing={2}>
        {saveError ? <Alert severity="error">{saveError}</Alert> : null}
        {saved ? <Alert severity="success">{t('workspaces.saved')}</Alert> : null}
        <TextField
          error={errors.name !== undefined}
          label={t('workspaces.name')}
          required
          {...register('name', { required: t('workspaces.nameRequired') })}
        />
        <TextField
          label={t('workspaces.description')}
          minRows={3}
          multiline
          {...register('description')}
        />
        <Button disabled={isSubmitting} type="submit" variant="contained">
          {t('workspaces.save')}
        </Button>
      </Stack>
      <Divider />
      <WorkspaceMemberManager workspaceId={workspaceId} />
    </Stack>
  )
}
