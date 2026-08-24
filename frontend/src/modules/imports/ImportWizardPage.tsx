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
import { uploadImport } from './importApi'

export function ImportWizardPage() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const [file, setFile] = useState<File | null>(null)
  const mutation = useMutation({
    mutationFn: (selected: File) => uploadImport(workspaceId!, selected),
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
      <Stepper activeStep={mutation.data ? 1 : 0} alternativeLabel sx={{ overflowX: 'auto', pb: 1 }}>
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
          <Alert severity="info">{t('imports.mappingNext')}</Alert>
        </Stack>
      ) : null}
    </Stack>
  )
}
