import { CloudUploadOutlined, LockOpenOutlined, LockOutlined } from '@mui/icons-material'
import { Alert, Button, Card, CardActions, CardContent, Chip, CircularProgress, Collapse, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { AcceptancePanel } from '../acceptance/AcceptancePanel'
import { DeliverablesPanel } from '../deliverables/DeliverablesPanel'
import { ImportWizard } from '../imports/ImportWizardPage'
import { createPhase, listPhases, setPhaseLocked, updatePhaseStatus, type Phase, type PhaseStatus } from './phaseApi'

interface CreateValues { name: string; description: string; sequenceNumber: number }

const statuses: PhaseStatus[] = ['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'ARCHIVED']

function PhaseCard({ phase }: { phase: Phase }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<PhaseStatus>(phase.status)
  const [error, setError] = useState<string | null>(null)
  const [importing, setImporting] = useState(false)
  const refresh = async () => queryClient.invalidateQueries({ queryKey: ['phases', phase.workspace_id] })
  const statusMutation = useMutation({
    mutationFn: () => updatePhaseStatus(phase, status), onSuccess: refresh,
  })
  const lockMutation = useMutation({
    mutationFn: () => setPhaseLocked(phase.id, !phase.is_locked), onSuccess: refresh,
  })
  const run = async (operation: () => Promise<unknown>) => {
    setError(null)
    try { await operation() } catch (caught) {
      setError(caught instanceof ApiError && caught.code === 'PERMISSION_DENIED'
        ? t('phases.permissionDenied') : t('phases.saveFailed'))
    }
  }
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography component="h2" variant="h5">{phase.sequence_number}. {phase.name}</Typography>
            <Chip color={phase.is_locked ? 'warning' : 'success'} icon={phase.is_locked ? <LockOutlined /> : <LockOpenOutlined />} label={phase.is_locked ? t('phases.locked') : t('phases.open')} />
          </Stack>
          {phase.description ? <Typography color="text.secondary">{phase.description}</Typography> : null}
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField disabled={phase.is_locked} label={t('phases.statusLabel')} onChange={(event) => setStatus(event.target.value as PhaseStatus)} select value={status}>
            {statuses.map((value) => <MenuItem key={value} value={value}>{t(`phases.status.${value}`)}</MenuItem>)}
          </TextField>
          <DeliverablesPanel locked={phase.is_locked} phaseId={phase.id} workspaceId={phase.workspace_id} />
          <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}>
            <Typography color="text.secondary" variant="body2">{t('imports.phaseContextHint')}</Typography>
            <Button disabled={phase.is_locked} onClick={() => setImporting((value) => !value)} startIcon={<CloudUploadOutlined />} variant="outlined">
              {t('imports.openInPhase')}
            </Button>
          </Stack>
          <Collapse in={importing && !phase.is_locked}>
            <ImportWizard
              description={t('imports.phaseDescription', { phase: phase.name })}
              onComplete={() => setImporting(false)}
              title={t('imports.phaseTitle', { phase: phase.name })}
              workspaceId={phase.workspace_id}
            />
          </Collapse>
          <AcceptancePanel phaseId={phase.id} workspaceId={phase.workspace_id} />
        </Stack>
      </CardContent>
      <CardActions>
        <Button disabled={phase.is_locked || status === phase.status || statusMutation.isPending} onClick={() => void run(() => statusMutation.mutateAsync())}>{t('phases.saveStatus')}</Button>
        <Button color={phase.is_locked ? 'warning' : 'primary'} disabled={lockMutation.isPending} onClick={() => void run(() => lockMutation.mutateAsync())}>{phase.is_locked ? t('phases.unlock') : t('phases.lock')}</Button>
      </CardActions>
    </Card>
  )
}

export function PhaseListPage() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const { handleSubmit, register, reset, formState } = useForm<CreateValues>({ defaultValues: { name: '', description: '', sequenceNumber: 1 } })
  const phases = useQuery({ queryKey: ['phases', workspaceId], queryFn: () => listPhases(workspaceId ?? ''), enabled: workspaceId !== undefined })
  const create = useMutation({
    mutationFn: (values: CreateValues) => createPhase(workspaceId ?? '', { name: values.name.trim(), description: values.description.trim() || null, sequence_number: Number(values.sequenceNumber) }),
    onSuccess: async () => { reset(); await queryClient.invalidateQueries({ queryKey: ['phases', workspaceId] }) },
  })
  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />
  const submit = handleSubmit(async (values) => {
    setError(null)
    try { await create.mutateAsync(values) } catch (caught) {
      setError(caught instanceof ApiError && caught.code === 'RESOURCE_CONFLICT' ? t('phases.sequenceConflict') : t('phases.saveFailed'))
    }
  })
  return (
    <Stack spacing={3}>
      <Stack spacing={0.5}><Typography component="h1" variant="h1">{t('phases.title')}</Typography><Typography color="text.secondary">{t('phases.description')}</Typography></Stack>
      <Card><CardContent><Stack component="form" onSubmit={(event) => void submit(event)} spacing={2}>
        <Typography component="h2" variant="h5">{t('phases.create')}</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}
        <TextField label={t('phases.name')} required {...register('name', { required: true })} />
        <TextField label={t('phases.descriptionLabel')} multiline {...register('description')} />
        <TextField label={t('phases.sequence')} type="number" {...register('sequenceNumber', { valueAsNumber: true, min: 1 })} />
        <Button disabled={formState.isSubmitting} type="submit" variant="contained">{t('phases.add')}</Button>
      </Stack></CardContent></Card>
      {phases.isPending ? <CircularProgress aria-label={t('phases.loading')} /> : null}
      {phases.isError ? <Alert severity="error">{t('phases.loadFailed')}</Alert> : null}
      {phases.data?.length === 0 ? <Alert severity="info">{t('phases.empty')}</Alert> : null}
      {phases.data?.map((phase) => <PhaseCard key={phase.id} phase={phase} />)}
    </Stack>
  )
}
