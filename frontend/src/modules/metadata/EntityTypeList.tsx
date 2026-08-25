import {
  Alert,
  Button,
  Card,
  CardActions,
  CardContent,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate, useParams } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { createEntityType, listEntityTypes } from './metadataApi'

interface FormValues {
  name: string
  pluralName: string
  description: string
}

export function EntityTypeList() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [mutationError, setMutationError] = useState<string | null>(null)
  const entityTypes = useQuery({
    queryKey: ['entity-types', workspaceId],
    queryFn: () => listEntityTypes(workspaceId ?? ''),
    enabled: workspaceId !== undefined,
  })
  const { handleSubmit, register, reset, formState } = useForm<FormValues>({
    defaultValues: { name: '', pluralName: '', description: '' },
  })
  const create = useMutation({
    mutationFn: (values: FormValues) =>
      createEntityType(workspaceId ?? '', {
        name: values.name.trim(),
        plural_name: values.pluralName.trim() || undefined,
        description: values.description.trim() || undefined,
        configuration: {},
      }),
    onSuccess: async () => {
      reset()
      await queryClient.invalidateQueries({ queryKey: ['entity-types', workspaceId] })
    },
  })

  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />

  const submit = handleSubmit(async (values) => {
    setMutationError(null)
    try {
      await create.mutateAsync(values)
    } catch (error) {
      setMutationError(
        error instanceof ApiError && error.code === 'RESOURCE_CONFLICT'
          ? t('metadata.duplicateKey')
          : t('metadata.saveFailed'),
      )
    }
  })

  return (
    <Stack spacing={3}>
      <Typography component="h1" variant="h1">{t('metadata.title')}</Typography>
      <Stack component="form" onSubmit={(event) => void submit(event)} spacing={2}>
        <Typography component="h2" variant="h5">{t('metadata.createType')}</Typography>
        {mutationError ? <Alert severity="error">{mutationError}</Alert> : null}
        <TextField label={t('metadata.name')} required {...register('name', { required: true })} />
        <TextField label={t('metadata.pluralName')} {...register('pluralName')} />
        <TextField label={t('metadata.description')} multiline {...register('description')} />
        <Button disabled={formState.isSubmitting} type="submit" variant="contained">
          {t('metadata.create')}
        </Button>
      </Stack>
      {entityTypes.isPending ? <CircularProgress aria-label={t('metadata.loading')} /> : null}
      {entityTypes.isError ? <Alert severity="error">{t('metadata.loadFailed')}</Alert> : null}
      {entityTypes.data?.items.length === 0 ? <Alert severity="info">{t('metadata.empty')}</Alert> : null}
      {entityTypes.data?.items.map((entityType) => (
        <Card key={entityType.id} variant="outlined">
          <CardContent>
            <Typography component="h2" variant="h5">{entityType.name}</Typography>
            {entityType.description ? (
              <Typography color="text.secondary">{entityType.description}</Typography>
            ) : null}
          </CardContent>
          <CardActions>
            <Button onClick={() => void navigate(`/workspaces/${workspaceId}/metadata/${entityType.id}`)}>
              {t('metadata.edit')}
            </Button>
          </CardActions>
        </Card>
      ))}
    </Stack>
  )
}
