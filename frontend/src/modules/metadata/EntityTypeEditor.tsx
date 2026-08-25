import { Alert, Button, CircularProgress, Divider, List, ListItem, ListItemText, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { AttributeDefinitionEditor } from './AttributeDefinitionEditor'
import { getEntityType, listAttributes, updateEntityType } from './metadataApi'

interface FormValues { name: string; pluralName: string; description: string }

export function EntityTypeEditor() {
  const { t } = useTranslation()
  const { entityTypeId } = useParams()
  const queryClient = useQueryClient()
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const entityType = useQuery({ queryKey: ['entity-type', entityTypeId], queryFn: () => getEntityType(entityTypeId ?? ''), enabled: entityTypeId !== undefined })
  const attributes = useQuery({ queryKey: ['attributes', entityTypeId], queryFn: () => listAttributes(entityTypeId ?? ''), enabled: entityTypeId !== undefined })
  const { handleSubmit, register, reset, formState } = useForm<FormValues>()
  useEffect(() => {
    if (entityType.data) reset({ name: entityType.data.name, pluralName: entityType.data.plural_name ?? '', description: entityType.data.description ?? '' })
  }, [entityType.data, reset])
  const update = useMutation({
    mutationFn: (values: FormValues) => updateEntityType(entityTypeId ?? '', {
      name: values.name.trim(), plural_name: values.pluralName.trim() || null,
      description: values.description.trim() || null,
      configuration: entityType.data?.configuration ?? {}, version: entityType.data?.version ?? 0,
    }),
    onSuccess: (value) => { queryClient.setQueryData(['entity-type', entityTypeId], value); setSaveMessage(t('metadata.saved')) },
  })
  if (entityTypeId === undefined) return <Navigate replace to="/workspaces" />
  if (entityType.isPending) return <CircularProgress aria-label={t('metadata.loading')} />
  if (entityType.isError) return <Alert severity="error">{t('metadata.loadFailed')}</Alert>
  const submit = handleSubmit(async (values) => {
    setSaveMessage(null)
    try { await update.mutateAsync(values) } catch (error) {
      setSaveMessage(error instanceof ApiError && error.code === 'STALE_VERSION' ? t('metadata.staleVersion') : t('metadata.saveFailed'))
    }
  })
  return (
    <Stack spacing={3}>
      <Typography component="h1" variant="h1">{entityType.data.name}</Typography>
      <Stack component="form" onSubmit={(event) => void submit(event)} spacing={2}>
        {saveMessage ? <Alert severity={update.isError ? 'error' : 'success'}>{saveMessage}</Alert> : null}
        <TextField label={t('metadata.name')} required {...register('name', { required: true })} />
        <TextField label={t('metadata.pluralName')} {...register('pluralName')} />
        <TextField label={t('metadata.description')} multiline {...register('description')} />
        <Button disabled={formState.isSubmitting} type="submit" variant="contained">{t('metadata.save')}</Button>
      </Stack>
      <Divider />
      <Typography component="h2" variant="h5">{t('metadata.attributes')}</Typography>
      {attributes.isError ? <Alert severity="error">{t('metadata.attributesLoadFailed')}</Alert> : null}
      {attributes.data?.length === 0 ? <Alert severity="info">{t('metadata.noAttributes')}</Alert> : null}
      <List>{attributes.data?.map((attribute) => <ListItem key={attribute.id} divider><ListItemText primary={attribute.label} secondary={attribute.data_type} /></ListItem>)}</List>
      <Divider />
      <AttributeDefinitionEditor entityTypeId={entityTypeId} />
    </Stack>
  )
}
