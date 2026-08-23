import { SaveOutlined } from '@mui/icons-material'
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'

import { ApiError } from '../../api/client'
import { createFormInstance, renderForm, saveFormInstance } from './formApi'
import { DynamicFieldRenderer } from './DynamicFieldRenderer'
import type { FormInstance, FormRenderContract } from './types'

interface DynamicFormRendererProps {
  formId: string
  entityId?: string
  canEdit: boolean
}

function editableDefaults(contract: FormRenderContract): Record<string, unknown> {
  return Object.fromEntries(
    contract.sections.flatMap((section) =>
      section.fields
        .filter((field) => field.visible && !field.read_only)
        .map((field) => [field.key, field.has_value ? field.value : null]),
    ),
  )
}

function fieldErrors(error: ApiError): { field: string; code: string }[] {
  const fields = error.details.fields
  if (!Array.isArray(fields)) return []
  return fields.flatMap((item) => {
    if (typeof item !== 'object' || item === null) return []
    const detail = item as Record<string, unknown>
    if (typeof detail.field === 'string' && typeof detail.code === 'string') {
      return [{ field: detail.field, code: detail.code }]
    }
    return []
  })
}

function FormEditor({ contract, entityId, canEdit }: { contract: FormRenderContract; entityId?: string; canEdit: boolean }) {
  const { t } = useTranslation()
  const [instance, setInstance] = useState<FormInstance | null>(null)
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [formError, setFormError] = useState<string | null>(null)
  const { control, handleSubmit, setError } = useForm<Record<string, unknown>>({
    defaultValues: editableDefaults(contract),
  })

  const save = async (values: Record<string, unknown>) => {
    if (entityId === undefined) return
    setSaveState('saving')
    setFormError(null)
    try {
      const activeInstance = instance ?? await createFormInstance(contract.form.id, entityId)
      const saved = await saveFormInstance(activeInstance.id, values, activeInstance.version)
      setInstance(saved)
      setSaveState('saved')
    } catch (error) {
      setSaveState('error')
      if (error instanceof ApiError && error.code === 'VALIDATION_ERROR') {
        const errors = fieldErrors(error)
        for (const detail of errors) {
          const topLevelField = detail.field.split('.')[0]
          setError(topLevelField, { message: t(`forms.validation.${detail.code}`, { defaultValue: t('forms.validation.invalid') }) })
        }
        setFormError(t('forms.validationFailed'))
      } else if (error instanceof ApiError && error.code === 'STALE_VERSION') {
        setFormError(t('forms.staleVersion'))
      } else {
        setFormError(t('forms.saveFailed'))
      }
    }
  }

  return (
    <Stack component="form" noValidate onSubmit={(event) => void handleSubmit(save)(event)} spacing={3}>
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between' }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Typography component="h2" variant="h2">{contract.form.name}</Typography>
          <Chip label={t('forms.version', { version: contract.form.version_number })} size="small" variant="outlined" />
        </Stack>
        {canEdit && entityId !== undefined ? (
          <Button disabled={saveState === 'saving'} startIcon={<SaveOutlined />} type="submit" variant="contained">
            {saveState === 'saving' ? t('forms.saving') : t('forms.saveDraft')}
          </Button>
        ) : null}
      </Stack>
      {formError ? <Alert severity="error">{formError}</Alert> : null}
      {saveState === 'saved' ? <Alert severity="success">{t('forms.saved')}</Alert> : null}
      {contract.sections.map((section, sectionIndex) => (
        <Card component="section" key={section.key ?? `section-${sectionIndex}`}>
          <CardContent>
            <Stack spacing={2.5}>
              {section.label ? <Typography component="h3" variant="h6">{section.label}</Typography> : null}
              {section.fields.map((field) => (
                <Controller
                  control={control}
                  key={field.key}
                  name={field.key}
                  render={({ field: controller, fieldState }) => (
                    <DynamicFieldRenderer
                      error={fieldState.error?.message}
                      field={{ ...field, read_only: field.read_only || !canEdit }}
                      onChange={controller.onChange}
                      value={field.read_only ? field.value : controller.value}
                    />
                  )}
                />
              ))}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  )
}

export function DynamicFormRenderer({ formId, entityId, canEdit }: DynamicFormRendererProps) {
  const { t } = useTranslation()
  const contract = useQuery({
    queryKey: ['form-render', formId, entityId],
    queryFn: () => renderForm(formId, entityId),
  })
  if (contract.isPending) return <CircularProgress aria-label={t('forms.loading')} />
  if (contract.isError) return <Alert severity="error">{t('forms.loadFailed')}</Alert>
  return <FormEditor canEdit={canEdit} contract={contract.data} entityId={entityId} />
}
