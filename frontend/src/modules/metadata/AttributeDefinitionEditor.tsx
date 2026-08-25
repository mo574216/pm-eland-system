import {
  Alert,
  Button,
  Checkbox,
  FormControlLabel,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { useTranslation } from 'react-i18next'

import { ApiError } from '../../api/client'
import { createAttribute, type AttributeDataType } from './metadataApi'

const dataTypes: AttributeDataType[] = [
  'TEXT', 'RICH_TEXT', 'INTEGER', 'DECIMAL', 'BOOLEAN', 'DATE', 'DATETIME',
  'ENUM', 'MULTI_ENUM', 'USER_REFERENCE', 'ENTITY_REFERENCE', 'FILE_REFERENCE',
  'JSON', 'TABLE',
]

interface FormValues {
  label: string
  dataType: AttributeDataType
  isRequired: boolean
  isReadOnly: boolean
  displayOrder: number
  enumOptions: string
}

export function AttributeDefinitionEditor({ entityTypeId }: { entityTypeId: string }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const { control, handleSubmit, register, reset, formState } = useForm<FormValues>({
    defaultValues: {
      label: '', dataType: 'TEXT', isRequired: false, isReadOnly: false,
      displayOrder: 0, enumOptions: '',
    },
  })
  const dataType = useWatch({ control, name: 'dataType' })
  const create = useMutation({
    mutationFn: (values: FormValues) => {
      const options = values.enumOptions.split('\n').map((value) => value.trim()).filter(Boolean)
      return createAttribute(entityTypeId, {
        label: values.label.trim(),
        data_type: values.dataType,
        is_required: values.isRequired,
        is_read_only: values.isReadOnly,
        display_order: Number(values.displayOrder),
        validation_config: {},
        display_config: ['ENUM', 'MULTI_ENUM'].includes(values.dataType)
          ? { options: options.map((value) => ({ value, label: value })) }
          : {},
        inheritance_config: {},
      })
    },
    onSuccess: async () => {
      reset()
      await queryClient.invalidateQueries({ queryKey: ['attributes', entityTypeId] })
    },
  })
  const submit = handleSubmit(async (values) => {
    setErrorMessage(null)
    try {
      await create.mutateAsync(values)
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError && error.code === 'RESOURCE_CONFLICT'
          ? t('metadata.duplicateKey')
          : t('metadata.invalidAttribute'),
      )
    }
  })

  return (
    <Stack component="form" onSubmit={(event) => void submit(event)} spacing={2}>
      <Typography component="h2" variant="h5">{t('metadata.addAttribute')}</Typography>
      {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
      <TextField label={t('metadata.label')} required {...register('label', { required: true })} />
      <TextField label={t('metadata.dataType')} select {...register('dataType')}>
        {dataTypes.map((value) => <MenuItem key={value} value={value}>{value}</MenuItem>)}
      </TextField>
      {dataType === 'ENUM' || dataType === 'MULTI_ENUM' ? (
        <TextField label={t('metadata.enumOptions')} helperText={t('metadata.enumOptionsHelp')} multiline required {...register('enumOptions', { required: true })} />
      ) : null}
      <TextField label={t('metadata.displayOrder')} type="number" {...register('displayOrder', { valueAsNumber: true, min: 0 })} />
      <FormControlLabel control={<Checkbox {...register('isRequired')} />} label={t('metadata.required')} />
      <FormControlLabel control={<Checkbox {...register('isReadOnly')} />} label={t('metadata.readOnly')} />
      <Button disabled={formState.isSubmitting} type="submit" variant="contained">{t('metadata.add')}</Button>
    </Stack>
  )
}
