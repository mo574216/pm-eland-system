import { CloudUploadOutlined, TableViewOutlined } from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { assignImportProfile, dryRunImport, uploadImport } from './importApi'
import { ImportConflictResolver } from './ImportConflictResolver'
import { ImportDryRunSummary } from './ImportDryRunSummary'
import { ImportMappingStep } from './ImportMappingStep'
import type { ImportProfile, ImportResolutionResult } from './types'

export function ImportWizardPage() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const [file, setFile] = useState<File | null>(null)
  const [savedProfile, setSavedProfile] = useState<ImportProfile | null>(null)
  const [resolutionState, setResolutionState] = useState<ImportResolutionResult | null>(null)
  const mutation = useMutation({
    mutationFn: (selected: File) => uploadImport(workspaceId!, selected),
  })
  const profileAssignment = useMutation({
    mutationFn: async (profile: ImportProfile) => {
      if (!mutation.data) throw new Error('Import upload is required')
      await assignImportProfile(mutation.data.import_job_id, profile.id)
      return profile
    },
    onSuccess: setSavedProfile,
  })
  const dryRun = useMutation({
    mutationFn: () => {
      if (!mutation.data) throw new Error('Import upload is required')
      return dryRunImport(mutation.data.import_job_id)
    },
  })
  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />

  const steps = [
    t('imports.steps.upload'),
    t('imports.steps.inspect'),
    t('imports.steps.mapping'),
    t('imports.steps.dryRun'),
    t('imports.steps.conflicts'),
    t('imports.steps.commit'),
    t('imports.steps.complete'),
  ]
  const errorCode = mutation.error instanceof ApiError ? mutation.error.code : null

  return (
    <Stack spacing={3}>
      <Box>
        <Typography component="h1" variant="h1">{t('imports.title')}</Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>{t('imports.description')}</Typography>
      </Box>
      <Stepper activeStep={resolutionState?.unresolved === 0 || dryRun.data?.status === 'READY_TO_COMMIT' ? 4 : dryRun.data ? 3 : savedProfile ? 2 : mutation.data ? 1 : 0} alternativeLabel sx={{ overflowX: 'auto', pb: 1 }}>
        {steps.map((label) => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
      </Stepper>
      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Typography component="h2" variant="h2">{t('imports.uploadTitle')}</Typography>
            <Typography color="text.secondary">{t('imports.uploadHint')}</Typography>
            <Button component="label" startIcon={<CloudUploadOutlined />} variant="outlined">
              {t('imports.chooseFile')}
              <input
                hidden
                accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                type="file"
                onChange={(event) => {
                  setFile(event.target.files?.[0] ?? null)
                  setSavedProfile(null)
                  profileAssignment.reset()
                  dryRun.reset()
                  setResolutionState(null)
                  mutation.reset()
                }}
              />
            </Button>
            {file ? <Chip label={`${t('imports.selectedFile')}: ${file.name}`} /> : null}
            <Button
              disabled={!file || mutation.isPending}
              onClick={() => { if (file) mutation.mutate(file) }}
              variant="contained"
            >
              {mutation.isPending ? <CircularProgress color="inherit" size={22} /> : t('imports.inspect')}
            </Button>
            {mutation.isError ? (
              <Alert severity="error">
                {errorCode === 'FILE_TOO_LARGE' ? t('imports.fileTooLarge') : t('imports.uploadFailed')}
              </Alert>
            ) : null}
          </Stack>
        </CardContent>
      </Card>
      {mutation.data ? (
        <Stack spacing={2}>
          <Alert severity="success">{t('imports.inspectionReady')}</Alert>
          {mutation.data.sheets.map((sheet) => (
            <Card key={sheet.name}>
              <CardContent>
                <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 2 }}>
                  <TableViewOutlined color="primary" />
                  <Typography component="h2" variant="h2">{sheet.name}</Typography>
                  <Chip label={`${sheet.row_count.toLocaleString('fa-IR')} ${t('imports.rows')}`} size="small" />
                </Stack>
                <Divider sx={{ mb: 2 }} />
                <TableContainer>
                  <Table size="small">
                    <TableHead><TableRow><TableCell>{t('imports.column')}</TableCell><TableCell>{t('imports.samples')}</TableCell></TableRow></TableHead>
                    <TableBody>
                      {sheet.columns.map((column) => (
                        <TableRow key={column.name}>
                          <TableCell sx={{ fontWeight: 800 }}>{column.name}</TableCell>
                          <TableCell>{column.sample_values.map(String).join('، ') || t('imports.noSample')}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          ))}
          {savedProfile ? (
            <Stack spacing={2}>
              <Alert severity="success">
                {t('imports.profileSaved', { name: savedProfile.name })} {t('imports.dryRunNext')}
              </Alert>
              {!dryRun.data ? (
                <Button
                  disabled={dryRun.isPending}
                  onClick={() => { setResolutionState(null); dryRun.mutate() }}
                  variant="contained"
                >
                  {dryRun.isPending ? <CircularProgress color="inherit" size={22} /> : t('imports.runDryRun')}
                </Button>
              ) : null}
              {dryRun.isError ? <Alert severity="error">{t('imports.dryRunFailed')}</Alert> : null}
            </Stack>
          ) : profileAssignment.isPending ? (
            <Alert icon={<CircularProgress size={20} />} severity="info">
              {t('imports.assigningProfile')}
            </Alert>
          ) : profileAssignment.isError ? (
            <Stack spacing={1.5}>
              <Alert severity="error">{t('imports.profileAssignmentFailed')}</Alert>
              <Button
                onClick={() => {
                  if (profileAssignment.variables) profileAssignment.mutate(profileAssignment.variables)
                }}
                variant="outlined"
              >
                {t('imports.retry')}
              </Button>
            </Stack>
          ) : (
            <ImportMappingStep
              inspection={mutation.data}
              onSaved={(profile) => profileAssignment.mutate(profile)}
              sourceType={file?.name.toLowerCase().endsWith('.xlsx') ? 'XLSX' : 'CSV'}
              workspaceId={workspaceId}
            />
          )}
          {dryRun.data ? <ImportDryRunSummary result={dryRun.data} /> : null}
          {dryRun.data && dryRun.data.summary.conflicts > 0 ? (
            <ImportConflictResolver
              importJobId={dryRun.data.import_job_id}
              onStatusChange={setResolutionState}
            />
          ) : null}
          {resolutionState?.unresolved === 0 || dryRun.data?.status === 'READY_TO_COMMIT' ? (
            <Alert severity="success">{t('imports.conflictsResolved')}</Alert>
          ) : null}
        </Stack>
      ) : null}
    </Stack>
  )
}
