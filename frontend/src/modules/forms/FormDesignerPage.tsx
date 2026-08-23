import {
  Alert,
  Button,
  Card,
  CardActions,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Navigate, useParams } from 'react-router-dom'

import { ApiError } from '../../api/client'
import { listAttributes, listEntityTypes } from '../metadata/metadataApi'
import { DynamicFormRenderer } from './DynamicFormRenderer'
import { addFormField, createForm, getForm, listForms, updateFormSections } from './formApi'
import type { FormFieldType } from './types'

const fieldTypes: FormFieldType[] = [
  'TEXT', 'RICH_TEXT', 'INTEGER', 'DECIMAL', 'BOOLEAN', 'DATE', 'DATETIME', 'ENUM',
  'MULTI_ENUM', 'USER_REFERENCE', 'ENTITY_REFERENCE', 'FILE_REFERENCE', 'TABLE',
]

interface CreateValues {
  key: string
  name: string
  description: string
  entityTypeId: string
}

interface SectionValues {
  key: string
  label: string
  displayOrder: number
}

interface FieldValues {
  key: string
  label: string
  fieldType: FormFieldType
  attributeId: string
  sectionKey: string
  displayOrder: number
  required: boolean
  readOnly: boolean
  options: string
  inheritanceSourcePath: string
  inheritanceStaticValue: string
  inheritanceMode: 'EDITABLE_DEFAULT' | 'READ_ONLY'
}

function DraftDesigner({ formId }: { formId: string }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [showPreview, setShowPreview] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)
  const definition = useQuery({ queryKey: ['form-definition', formId], queryFn: () => getForm(formId) })
  const attributes = useQuery({
    queryKey: ['attributes', definition.data?.entity_type_id, 'form-designer'],
    queryFn: () => listAttributes(definition.data?.entity_type_id ?? ''),
    enabled: definition.data?.entity_type_id !== null && definition.data?.entity_type_id !== undefined,
  })
  const sectionForm = useForm<SectionValues>({ defaultValues: { key: '', label: '', displayOrder: 0 } })
  const fieldForm = useForm<FieldValues>({
    defaultValues: {
      key: '', label: '', fieldType: 'TEXT', attributeId: '', sectionKey: '', displayOrder: 0,
      required: false, readOnly: false, options: '', inheritanceSourcePath: '',
      inheritanceStaticValue: '', inheritanceMode: 'EDITABLE_DEFAULT',
    },
  })
  const attributeId = useWatch({ control: fieldForm.control, name: 'attributeId' })
  const fieldType = useWatch({ control: fieldForm.control, name: 'fieldType' })
  const sectionKey = useWatch({ control: fieldForm.control, name: 'sectionKey' })
  const required = useWatch({ control: fieldForm.control, name: 'required' })
  const readOnly = useWatch({ control: fieldForm.control, name: 'readOnly' })
  const inheritanceMode = useWatch({ control: fieldForm.control, name: 'inheritanceMode' })
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ['form-definition', formId] })
    await queryClient.invalidateQueries({ queryKey: ['form-render', formId] })
  }
  const addSection = useMutation({
    mutationFn: (values: SectionValues) => updateFormSections(formId, [
      ...(definition.data?.schema_json.sections ?? []),
      { key: values.key.trim(), label: values.label.trim(), display_order: values.displayOrder, configuration: {} },
    ]),
    onSuccess: async () => { sectionForm.reset(); await refresh() },
  })
  const addField = useMutation({
    mutationFn: (values: FieldValues) => {
      const optionValues = values.options.split('\n').map((value) => value.trim()).filter(Boolean)
      const configuration: Record<string, unknown> = optionValues.length > 0
        ? { options: optionValues.map((value) => ({ value, label: value })) }
        : {}
      const inheritance_rule: Record<string, unknown> = values.inheritanceStaticValue.trim()
        ? { version: 1, static_value: values.inheritanceStaticValue, mode: values.inheritanceMode }
        : values.inheritanceSourcePath.trim()
          ? { version: 1, source_path: values.inheritanceSourcePath.trim(), mode: values.inheritanceMode }
          : {}
      return addFormField(formId, {
        key: values.key.trim(), label: values.label.trim(), field_type: values.fieldType,
        attribute_definition_id: values.attributeId || null,
        section_key: values.sectionKey || null, display_order: values.displayOrder,
        is_required: values.required, is_read_only: values.readOnly, configuration,
        visibility_rule: {}, validation_rule: {}, inheritance_rule,
      })
    },
    onSuccess: async () => { fieldForm.reset(); await refresh() },
  })
  const runMutation = async (action: () => Promise<unknown>) => {
    setMutationError(null)
    try { await action() } catch (error) {
      setMutationError(error instanceof ApiError && error.code === 'RESOURCE_CONFLICT'
        ? t('formDesigner.duplicate') : t('formDesigner.saveFailed'))
    }
  }

  if (definition.isPending) return <CircularProgress aria-label={t('formDesigner.loading')} />
  if (definition.isError) return <Alert severity="error">{t('formDesigner.loadFailed')}</Alert>
  if (definition.data.lifecycle_status !== 'DRAFT') return <Alert severity="info">{t('formDesigner.publishedImmutable')}</Alert>

  return (
    <Stack spacing={3}>
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography component="h2" variant="h2">{definition.data.name}</Typography>
        <Button onClick={() => setShowPreview((value) => !value)} variant="outlined">
          {showPreview ? t('formDesigner.closePreview') : t('formDesigner.preview')}
        </Button>
      </Stack>
      {mutationError ? <Alert severity="error">{mutationError}</Alert> : null}
      {showPreview ? <DynamicFormRenderer canEdit={false} formId={formId} /> : null}

      <Card>
        <CardContent>
          <Stack aria-label={t('formDesigner.addSection')} component="form" onSubmit={(event) => void sectionForm.handleSubmit((values) => runMutation(() => addSection.mutateAsync(values)))(event)} spacing={2}>
            <Typography component="h3" variant="h6">{t('formDesigner.addSection')}</Typography>
            <TextField label={t('formDesigner.key')} required {...sectionForm.register('key', { required: true, pattern: /^[a-z][a-z0-9_]*$/ })} />
            <TextField label={t('formDesigner.label')} required {...sectionForm.register('label', { required: true })} />
            <TextField label={t('formDesigner.order')} type="number" {...sectionForm.register('displayOrder', { valueAsNumber: true, min: 0 })} />
            <Button disabled={addSection.isPending} type="submit" variant="contained">{t('formDesigner.addSection')}</Button>
          </Stack>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Stack aria-label={t('formDesigner.addField')} component="form" onSubmit={(event) => void fieldForm.handleSubmit((values) => runMutation(() => addField.mutateAsync(values)))(event)} spacing={2}>
            <Typography component="h3" variant="h6">{t('formDesigner.addField')}</Typography>
            <FormControl fullWidth><InputLabel id="attribute-label">{t('formDesigner.attribute')}</InputLabel><Select
              label={t('formDesigner.attribute')} labelId="attribute-label" value={attributeId}
              onChange={(event) => {
                fieldForm.setValue('attributeId', event.target.value)
                const attribute = attributes.data?.find((item) => item.id === event.target.value)
                if (attribute && attribute.data_type !== 'JSON') {
                  fieldForm.setValue('key', attribute.key); fieldForm.setValue('label', attribute.label)
                  fieldForm.setValue('fieldType', attribute.data_type)
                }
              }}
            ><MenuItem value="">{t('formDesigner.noAttribute')}</MenuItem>{attributes.data?.map((attribute) => <MenuItem key={attribute.id} value={attribute.id}>{attribute.label}</MenuItem>)}</Select></FormControl>
            <TextField label={t('formDesigner.key')} required {...fieldForm.register('key', { required: true, pattern: /^[a-z][a-z0-9_]*$/ })} />
            <TextField label={t('formDesigner.label')} required {...fieldForm.register('label', { required: true })} />
            <FormControl fullWidth><InputLabel id="field-type-label">{t('formDesigner.fieldType')}</InputLabel><Select label={t('formDesigner.fieldType')} labelId="field-type-label" value={fieldType} onChange={(event) => fieldForm.setValue('fieldType', event.target.value)}>{fieldTypes.map((type) => <MenuItem key={type} value={type}>{type}</MenuItem>)}</Select></FormControl>
            <FormControl fullWidth><InputLabel id="section-label">{t('formDesigner.section')}</InputLabel><Select label={t('formDesigner.section')} labelId="section-label" value={sectionKey} onChange={(event) => fieldForm.setValue('sectionKey', event.target.value)}><MenuItem value="">{t('formDesigner.noSection')}</MenuItem>{definition.data.schema_json.sections.map((section) => <MenuItem key={section.key} value={section.key}>{section.label}</MenuItem>)}</Select></FormControl>
            <TextField label={t('formDesigner.order')} type="number" {...fieldForm.register('displayOrder', { valueAsNumber: true, min: 0 })} />
            <Stack direction="row"><FormControlLabel control={<Checkbox checked={required} onChange={(_, value) => fieldForm.setValue('required', value)} />} label={t('formDesigner.required')} /><FormControlLabel control={<Checkbox checked={readOnly} onChange={(_, value) => fieldForm.setValue('readOnly', value)} />} label={t('formDesigner.readOnly')} /></Stack>
            <TextField helperText={t('formDesigner.optionsHelp')} label={t('formDesigner.options')} multiline minRows={3} {...fieldForm.register('options')} />
            <TextField helperText={t('formDesigner.sourcePathHelp')} label={t('formDesigner.sourcePath')} {...fieldForm.register('inheritanceSourcePath')} />
            <TextField label={t('formDesigner.staticValue')} {...fieldForm.register('inheritanceStaticValue')} />
            <FormControl fullWidth><InputLabel id="inheritance-mode-label">{t('formDesigner.inheritanceMode')}</InputLabel><Select label={t('formDesigner.inheritanceMode')} labelId="inheritance-mode-label" value={inheritanceMode} onChange={(event) => fieldForm.setValue('inheritanceMode', event.target.value)}><MenuItem value="EDITABLE_DEFAULT">{t('formDesigner.editableDefault')}</MenuItem><MenuItem value="READ_ONLY">{t('formDesigner.readOnlyInherited')}</MenuItem></Select></FormControl>
            <Button disabled={addField.isPending} type="submit" variant="contained">{t('formDesigner.addField')}</Button>
          </Stack>
        </CardContent>
      </Card>
      <Stack spacing={1}>{definition.data.schema_json.sections.map((section) => <Card key={section.key} variant="outlined"><CardContent><Typography sx={{ fontWeight: 800 }}>{section.label}</Typography><Typography color="text.secondary" dir="ltr">{section.key}</Typography>{definition.data.fields.filter((field) => field.section_key === section.key).map((field) => <Chip key={field.id} label={`${field.label} · ${field.field_type}`} sx={{ m: 0.5 }} />)}</CardContent></Card>)}</Stack>
    </Stack>
  )
}

export function FormDesignerPage() {
  const { t } = useTranslation()
  const { workspaceId } = useParams()
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const forms = useQuery({ queryKey: ['forms', workspaceId], queryFn: () => listForms(workspaceId ?? ''), enabled: workspaceId !== undefined })
  const entityTypes = useQuery({ queryKey: ['entity-types', workspaceId], queryFn: () => listEntityTypes(workspaceId ?? ''), enabled: workspaceId !== undefined })
  const creation = useForm<CreateValues>({ defaultValues: { key: '', name: '', description: '', entityTypeId: '' } })
  const entityTypeId = useWatch({ control: creation.control, name: 'entityTypeId' })
  const create = useMutation({ mutationFn: (values: CreateValues) => createForm(workspaceId ?? '', { key: values.key.trim(), name: values.name.trim(), description: values.description.trim() || null, entity_type_id: values.entityTypeId }), onSuccess: async (form) => { creation.reset(); setSelectedId(form.id); await queryClient.invalidateQueries({ queryKey: ['forms', workspaceId] }) } })
  if (workspaceId === undefined) return <Navigate replace to="/workspaces" />
  const submit = creation.handleSubmit(async (values) => { setError(null); try { await create.mutateAsync(values) } catch { setError(t('formDesigner.saveFailed')) } })
  return <Stack spacing={3}><Typography component="h1" variant="h1">{t('formDesigner.title')}</Typography><Card><CardContent><Stack component="form" onSubmit={(event) => void submit(event)} spacing={2}><Typography component="h2" variant="h6">{t('formDesigner.create')}</Typography>{error ? <Alert severity="error">{error}</Alert> : null}<TextField label={t('formDesigner.key')} required {...creation.register('key', { required: true, pattern: /^[a-z][a-z0-9_]*$/ })} /><TextField label={t('formDesigner.name')} required {...creation.register('name', { required: true })} /><TextField label={t('formDesigner.description')} multiline {...creation.register('description')} /><FormControl fullWidth required><InputLabel id="form-entity-type-label">{t('formDesigner.entityType')}</InputLabel><Select label={t('formDesigner.entityType')} labelId="form-entity-type-label" value={entityTypeId} onChange={(event) => creation.setValue('entityTypeId', event.target.value, { shouldValidate: true })}>{entityTypes.data?.items.map((type) => <MenuItem key={type.id} value={type.id}>{type.name}</MenuItem>)}</Select></FormControl><Button disabled={create.isPending} type="submit" variant="contained">{t('formDesigner.create')}</Button></Stack></CardContent></Card>{forms.isPending ? <CircularProgress aria-label={t('formDesigner.loading')} /> : null}{forms.isError ? <Alert severity="error">{t('formDesigner.loadFailed')}</Alert> : null}<Stack spacing={1}>{forms.data?.items.map((form) => <Card key={form.id} variant="outlined"><CardContent><Typography component="h2" variant="h6">{form.name}</Typography><Chip label={form.lifecycle_status} size="small" /></CardContent><CardActions>{form.lifecycle_status === 'DRAFT' ? <Button onClick={() => setSelectedId(form.id)}>{t('formDesigner.design')}</Button> : null}</CardActions></Card>)}</Stack>{selectedId ? <DraftDesigner formId={selectedId} /> : null}</Stack>
}
