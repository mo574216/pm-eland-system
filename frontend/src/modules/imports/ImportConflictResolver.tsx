import {
  Alert,
  Button,
  ButtonGroup,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import {
  listImportConflicts,
  resolveImportConflict,
  resolveImportConflictsBulk,
} from './importApi'
import type { ImportConflictResolution, ImportResolutionResult } from './types'

interface Props {
  importJobId: string
  onStatusChange: (result: ImportResolutionResult) => void
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}

export function ImportConflictResolver({ importJobId, onStatusChange }: Props) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(25)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const queryKey = ['import-conflicts', importJobId, page, pageSize]
  const conflicts = useQuery({
    queryKey,
    queryFn: () => listImportConflicts(importJobId, page + 1, pageSize),
  })
  const refresh = async (result: ImportResolutionResult) => {
    setSelected(new Set())
    onStatusChange(result)
    await queryClient.invalidateQueries({ queryKey: ['import-conflicts', importJobId] })
  }
  const single = useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution: ImportConflictResolution }) => (
      resolveImportConflict(importJobId, id, resolution)
    ),
    onSuccess: refresh,
  })
  const bulk = useMutation({
    mutationFn: (resolution: ImportConflictResolution) => (
      resolveImportConflictsBulk(importJobId, [...selected], resolution)
    ),
    onSuccess: refresh,
  })
  const busy = single.isPending || bulk.isPending

  if (conflicts.isPending) return <CircularProgress aria-label={t('imports.loadingConflicts')} />
  if (conflicts.isError || !conflicts.data) {
    return <Alert severity="error">{t('imports.conflictsLoadFailed')}</Alert>
  }

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Typography component="h2" variant="h2">{t('imports.conflictTitle')}</Typography>
            <Chip
              color={conflicts.data.unresolved === 0 ? 'success' : 'warning'}
              label={t('imports.unresolvedCount', { count: conflicts.data.unresolved })}
              size="small"
            />
          </Stack>
          <Alert severity="warning">{t('imports.noDefaultResolution')}</Alert>
          {selected.size > 0 ? (
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
              <Typography>{t('imports.selectedCount', { count: selected.size })}</Typography>
              {(['MERGE', 'REPLACE', 'SKIP'] as const).map((resolution) => (
                <Button
                  color={resolution === 'REPLACE' ? 'error' : 'primary'}
                  disabled={busy}
                  key={resolution}
                  onClick={() => bulk.mutate(resolution)}
                  variant="outlined"
                >
                  {t(`imports.resolution.${resolution}`)}
                </Button>
              ))}
            </Stack>
          ) : null}
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" />
                <TableCell>{t('imports.errorRow')}</TableCell>
                <TableCell>{t('imports.conflictField')}</TableCell>
                <TableCell>{t('imports.existingValue')}</TableCell>
                <TableCell>{t('imports.importedValue')}</TableCell>
                <TableCell>{t('imports.decision')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {conflicts.data.items.map((conflict) => (
                <TableRow key={conflict.id}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selected.has(conflict.id)}
                      slotProps={{
                        input: {
                          'aria-label': t('imports.selectConflict', {
                            row: conflict.row_number ?? '',
                          }),
                        },
                      }}
                      onChange={(_, checked) => setSelected((current) => {
                        const next = new Set(current)
                        if (checked) next.add(conflict.id)
                        else next.delete(conflict.id)
                        return next
                      })}
                    />
                  </TableCell>
                  <TableCell>{conflict.row_number?.toLocaleString('fa-IR') ?? '—'}</TableCell>
                  <TableCell>{conflict.attribute_key ?? '—'}</TableCell>
                  <TableCell>{displayValue(conflict.existing_value)}</TableCell>
                  <TableCell>{displayValue(conflict.imported_value)}</TableCell>
                  <TableCell>
                    {conflict.resolution ? (
                      <Chip label={t(`imports.resolution.${conflict.resolution}`)} size="small" />
                    ) : (
                      <ButtonGroup disabled={busy} size="small" variant="outlined">
                        {(['MERGE', 'REPLACE', 'SKIP'] as const).map((resolution) => (
                          <Button
                            color={resolution === 'REPLACE' ? 'error' : 'primary'}
                            key={resolution}
                            onClick={() => single.mutate({ id: conflict.id, resolution })}
                          >
                            {t(`imports.resolution.${resolution}`)}
                          </Button>
                        ))}
                      </ButtonGroup>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={conflicts.data.total}
            onPageChange={(_, value) => { setPage(value); setSelected(new Set()) }}
            onRowsPerPageChange={(event) => {
              setPageSize(Number(event.target.value)); setPage(0); setSelected(new Set())
            }}
            page={page}
            rowsPerPage={pageSize}
            rowsPerPageOptions={[10, 25, 50, 100]}
          />
          {single.isError || bulk.isError ? (
            <Alert severity="error">{t('imports.conflictSaveFailed')}</Alert>
          ) : null}
        </Stack>
      </CardContent>
    </Card>
  )
}
