import { Alert, Card, CardContent, Chip, Grid, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

import type { ImportDryRunResult } from './types'

interface Props {
  result: ImportDryRunResult
}

export function ImportDryRunSummary({ result }: Props) {
  const { t } = useTranslation()
  const counters = [
    ['rows_read', result.summary.rows_read],
    ['rows_valid', result.summary.rows_valid],
    ['rows_invalid', result.summary.rows_invalid],
    ['records_to_create', result.summary.records_to_create],
    ['records_to_update', result.summary.records_to_update],
    ['records_unchanged', result.summary.records_unchanged],
    ['conflicts', result.summary.conflicts],
  ] as const

  return (
    <Card>
      <CardContent>
        <Stack spacing={2.5}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Typography component="h2" variant="h2">{t('imports.dryRunTitle')}</Typography>
            <Chip
              color={result.status === 'READY_FOR_REVIEW' ? 'success' : 'warning'}
              label={t(`imports.status.${result.status}`)}
              size="small"
            />
          </Stack>
          <Alert severity="info">{t('imports.noCanonicalChange')}</Alert>
          <Grid container spacing={1.5}>
            {counters.map(([key, value]) => (
              <Grid key={key} size={{ xs: 6, md: 3 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography color="text.secondary" variant="body2">{t(`imports.summary.${key}`)}</Typography>
                    <Typography sx={{ mt: 0.5 }} variant="h2">{value.toLocaleString('fa-IR')}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          {result.validation_errors.length > 0 ? (
            <Stack spacing={1}>
              <Typography component="h3" variant="h3">{t('imports.validationErrors')}</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('imports.errorRow')}</TableCell>
                    <TableCell>{t('imports.errorField')}</TableCell>
                    <TableCell>{t('imports.errorCode')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.validation_errors.map((error, index) => (
                    <TableRow key={`${error.row_number ?? 'mapping'}-${error.field}-${error.code}-${String(index)}`}>
                      <TableCell>{error.row_number?.toLocaleString('fa-IR') ?? t('imports.mapping')}</TableCell>
                      <TableCell>{error.field}</TableCell>
                      <TableCell>{error.code}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Stack>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  )
}
