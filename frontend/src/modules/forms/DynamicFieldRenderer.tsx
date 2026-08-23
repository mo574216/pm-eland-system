import { AddRounded, DeleteOutlineRounded, LockOutlined } from '@mui/icons-material'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useTranslation } from 'react-i18next'

import { normalizeOptions } from './fieldOptions'
import type { FormRenderField, TableColumn } from './types'

export interface DynamicFieldRendererProps {
  field: FormRenderField
  value: unknown
  onChange: (value: unknown) => void
  error?: string
}

function textValue(value: unknown): string | number {
  return typeof value === 'string' || typeof value === 'number' ? value : ''
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function columnsFrom(configuration: Record<string, unknown>): TableColumn[] {
  const columns = configuration.columns
  if (!Array.isArray(columns)) return []
  return columns.flatMap((column): TableColumn[] => {
    if (!isRecord(column) || typeof column.key !== 'string' || typeof column.type !== 'string' || column.type === 'TABLE') return []
    const supported = [
      'TEXT', 'RICH_TEXT', 'INTEGER', 'DECIMAL', 'BOOLEAN', 'DATE', 'DATETIME',
      'ENUM', 'MULTI_ENUM', 'USER_REFERENCE', 'ENTITY_REFERENCE', 'FILE_REFERENCE',
    ] as const
    if (!supported.includes(column.type as (typeof supported)[number])) return []
    return [{
      key: column.key,
      label: 'label' in column && typeof column.label === 'string' ? column.label : column.key,
      type: column.type as TableColumn['type'],
      required: 'required' in column && column.required === true,
      configuration: isRecord(column.configuration) ? column.configuration : {},
    }]
  })
}

function DynamicTableField({ field, value, onChange, error }: DynamicFieldRendererProps) {
  const { t } = useTranslation()
  const columns = columnsFrom(field.configuration)
  const rows = Array.isArray(value)
    ? value.filter((row): row is Record<string, unknown> => typeof row === 'object' && row !== null)
    : []
  if (columns.length === 0) return <Alert severity="warning">{t('forms.invalidTable')}</Alert>

  return (
    <Stack spacing={1.5}>
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography component="h3" sx={{ fontWeight: 800 }}>{field.label}</Typography>
        {!field.read_only ? (
          <Button
            onClick={() => onChange([...rows, Object.fromEntries(columns.map((column) => [column.key, null]))])}
            size="small"
            startIcon={<AddRounded />}
          >
            {t('forms.addRow')}
          </Button>
        ) : null}
      </Stack>
      {rows.length === 0 ? <Alert severity="info">{t('forms.emptyTable')}</Alert> : null}
      {rows.map((row, rowIndex) => (
        <Box key={rowIndex} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, p: 2 }}>
          <Stack spacing={2}>
            {columns.map((column) => (
              <DynamicFieldRenderer
                field={{
                  key: column.key,
                  label: column.label,
                  type: column.type,
                  required: column.required ?? false,
                  read_only: field.read_only,
                  visible: true,
                  value: row[column.key],
                  has_value: column.key in row,
                  value_source: field.value_source,
                  configuration: column.configuration ?? {},
                  visibility_rule: {},
                  validation_rule: {},
                }}
                key={column.key}
                onChange={(nextValue) => {
                  const nextRows = [...rows]
                  nextRows[rowIndex] = { ...row, [column.key]: nextValue }
                  onChange(nextRows)
                }}
                value={row[column.key]}
              />
            ))}
            {!field.read_only ? (
              <Button
                color="error"
                onClick={() => onChange(rows.filter((_, index) => index !== rowIndex))}
                size="small"
                startIcon={<DeleteOutlineRounded />}
                sx={{ alignSelf: 'flex-start' }}
              >
                {t('forms.removeRow')}
              </Button>
            ) : null}
          </Stack>
        </Box>
      ))}
      {error ? <FormHelperText error>{error}</FormHelperText> : null}
    </Stack>
  )
}

export function DynamicFieldRenderer({ field, value, onChange, error }: DynamicFieldRendererProps) {
  const { t } = useTranslation()
  if (!field.visible) return null

  const common = {
    disabled: field.read_only,
    error: Boolean(error),
    fullWidth: true,
    helperText: error,
    label: field.label,
    required: field.required,
  }
  const inherited = field.value_source === 'INHERITED'
  const decoration = inherited ? (
    <Chip icon={field.read_only ? <LockOutlined /> : undefined} label={t('forms.inherited')} size="small" variant="outlined" />
  ) : null

  let control
  if (field.type === 'BOOLEAN') {
    control = (
      <FormControl error={Boolean(error)}>
        <FormControlLabel
          control={<Checkbox checked={value === true} disabled={field.read_only} onChange={(_, checked) => onChange(checked)} />}
          label={`${field.label}${field.required ? ` (${t('forms.required')})` : ''}`}
        />
        {error ? <FormHelperText>{error}</FormHelperText> : null}
      </FormControl>
    )
  } else if (field.type === 'ENUM' || field.type === 'MULTI_ENUM') {
    const options = normalizeOptions(field.configuration.options)
    const multiple = field.type === 'MULTI_ENUM'
    control = (
      <FormControl disabled={field.read_only} error={Boolean(error)} fullWidth required={field.required}>
        <InputLabel id={`${field.key}-label`}>{field.label}</InputLabel>
        <Select
          label={field.label}
          labelId={`${field.key}-label`}
          multiple={multiple}
          onChange={(event) => onChange(event.target.value)}
          value={multiple ? (Array.isArray(value) ? value : []) : textValue(value)}
        >
          {options.map((option) => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
        </Select>
        {error ? <FormHelperText>{error}</FormHelperText> : null}
      </FormControl>
    )
  } else if (field.type === 'TABLE') {
    control = <DynamicTableField error={error} field={field} onChange={onChange} value={value} />
  } else {
    const inputType = field.type === 'INTEGER' || field.type === 'DECIMAL'
      ? 'number'
      : field.type === 'DATE'
        ? 'date'
        : field.type === 'DATETIME'
          ? 'datetime-local'
          : 'text'
    const multiline = field.type === 'RICH_TEXT' || field.configuration.multiline === true
    control = (
      <TextField
        {...common}
        minRows={multiline ? 4 : undefined}
        multiline={multiline}
        onChange={(event) => {
          if (field.type === 'INTEGER') onChange(event.target.value === '' ? null : Number.parseInt(event.target.value, 10))
          else if (field.type === 'DECIMAL') onChange(event.target.value === '' ? null : Number(event.target.value))
          else onChange(event.target.value)
        }}
        slotProps={{
          htmlInput: field.type === 'DECIMAL' ? { step: 'any' } : undefined,
          inputLabel:
            inputType === 'date' || inputType === 'datetime-local'
              ? { shrink: true }
              : undefined,
        }}
        type={inputType}
        value={textValue(value)}
      />
    )
  }

  return <Stack spacing={0.75}>{decoration}{control}</Stack>
}
