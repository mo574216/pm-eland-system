import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  CircularProgress,
  FormControl,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { listAttributes, listEntityTypes } from '../metadata/metadataApi'
import { createImportProfile, listImportProfiles } from './importApi'
import type {
  ImportMappingCreate,
  ImportProfile,
  ImportUploadResult,
  ImportTarget,
  MatchKey,
  MatchingStrategy,
} from './types'

type MatchingMode = MatchingStrategy['type']

interface Props {
  workspaceId: string
  sourceType: 'CSV' | 'XLSX'
  inspection: ImportUploadResult
  onSaved: (profile: ImportProfile) => void
}

function mappingTarget(value: string): ImportTarget {
  const [kind, id] = value.split(':', 2)
  return kind === 'attribute'
    ? { target_attribute_definition_id: id }
    : { target_system_field: id as 'name' | 'description' | 'parent_id' }
}

function matchKey(
  sourceSheet: string,
  sourceColumn: string,
  target: string,
): MatchKey | null {
  const parsed = mappingTarget(target)
  if (parsed.target_attribute_definition_id) {
    return { source_sheet: sourceSheet, source_column: sourceColumn, attribute_definition_id: parsed.target_attribute_definition_id }
  }
  if (parsed.target_system_field === 'name') {
    return { source_sheet: sourceSheet, source_column: sourceColumn, system_field: 'name' }
  }
  return null
}

export function ImportMappingStep({ workspaceId, sourceType, inspection, onSaved }: Props) {
  const { t } = useTranslation()
  const [sheetName, setSheetName] = useState(inspection.sheets[0]?.name ?? '')
  const [entityTypeId, setEntityTypeId] = useState('')
  const [profileName, setProfileName] = useState('')
  const [targets, setTargets] = useState<Record<string, string>>({})
  const [matchingMode, setMatchingMode] = useState<MatchingMode>('UNIQUE_ATTRIBUTE')
  const [keyColumns, setKeyColumns] = useState<string[]>([])
  const [parentColumn, setParentColumn] = useState('')
  const profiles = useQuery({
    queryKey: ['import-profiles', workspaceId],
    queryFn: () => listImportProfiles(workspaceId),
  })
  const entityTypes = useQuery({
    queryKey: ['entity-types', workspaceId, 'import-mapping'],
    queryFn: () => listEntityTypes(workspaceId),
  })
  const attributes = useQuery({
    queryKey: ['attributes', entityTypeId, 'import-mapping'],
    queryFn: () => listAttributes(entityTypeId),
    enabled: entityTypeId !== '',
  })
  const columns = useMemo(
    () => inspection.sheets.find((item) => item.name === sheetName)?.columns ?? [],
    [inspection.sheets, sheetName],
  )
  const mappings = useMemo<ImportMappingCreate[]>(() => columns.flatMap((column, index) => {
    const target = targets[column.name]
    if (!target) return []
    const parsedTarget = mappingTarget(target)
    const mapping: ImportMappingCreate = {
      source_sheet: sheetName,
      source_column: column.name,
      ...parsedTarget,
      transformation_config: {},
      display_order: index,
    }
    return [mapping]
  }), [columns, sheetName, targets])
  const keys = keyColumns.flatMap((column) => {
    const target = targets[column]
    const key = target ? matchKey(sheetName, column, target) : null
    return key ? [key] : []
  })
  const hasName = mappings.some((item) => item.target_system_field === 'name')
  const parentMapped = mappings.some(
    (item) => item.source_column === parentColumn && item.target_system_field === 'parent_id',
  )
  const strategyValid = matchingMode === 'ENTITY_ID'
    ? keyColumns.length === 1
    : matchingMode === 'UNIQUE_ATTRIBUTE'
      ? keys.length === 1 && keyColumns.length === 1
      : matchingMode === 'COMPOSITE_KEY'
        ? keys.length === keyColumns.length && keys.length >= 2
        : keys.length === 1 && keyColumns.length === 1 && parentColumn !== '' && parentMapped
  const mappingTargets = mappings.map(
    (item) => item.target_attribute_definition_id ?? item.target_system_field,
  )
  const targetsAreDistinct = new Set(mappingTargets).size === mappingTargets.length
  const mutation = useMutation({
    mutationFn: () => {
      const firstColumn = keyColumns[0]
      const firstKey = keys[0]
      if (!firstColumn || (matchingMode !== 'ENTITY_ID' && !firstKey)) {
        throw new Error('Invalid matching strategy')
      }
      const strategy: MatchingStrategy = matchingMode === 'ENTITY_ID'
        ? { type: 'ENTITY_ID', source_sheet: sheetName, source_column: firstColumn }
        : matchingMode === 'UNIQUE_ATTRIBUTE'
          ? { type: 'UNIQUE_ATTRIBUTE', key: firstKey }
          : matchingMode === 'COMPOSITE_KEY'
            ? { type: 'COMPOSITE_KEY', keys }
            : {
                type: 'PARENT_AND_KEY', parent_source_sheet: sheetName,
                parent_source_column: parentColumn, key: firstKey,
              }
      return createImportProfile(workspaceId, {
        entity_type_id: entityTypeId,
        name: profileName.trim(),
        description: null,
        source_type: sourceType,
        matching_strategy: strategy,
        configuration: { selected_sheet: sheetName },
        mappings,
      })
    },
    onSuccess: onSaved,
  })
  const canSave = profileName.trim() !== '' && entityTypeId !== '' && hasName && targetsAreDistinct
    && mappings.length > 0 && strategyValid && !mutation.isPending

  return (
    <Card>
      <CardContent>
        <Stack spacing={2.5}>
          <Typography component="h2" variant="h2">{t('imports.mappingTitle')}</Typography>
          {profiles.data?.items.some((item) => item.source_type === sourceType) ? (
            <FormControl fullWidth>
              <InputLabel id="stored-profile-label">{t('imports.storedProfile')}</InputLabel>
              <Select
                label={t('imports.storedProfile')}
                labelId="stored-profile-label"
                value=""
                onChange={(event) => {
                  const profile = profiles.data.items.find((item) => item.id === event.target.value)
                  if (profile) onSaved(profile)
                }}
              >
                {profiles.data.items.filter((item) => item.source_type === sourceType).map((item) => (
                  <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : null}
          <FormControl fullWidth>
            <InputLabel id="import-sheet-label">{t('imports.sheet')}</InputLabel>
            <Select label={t('imports.sheet')} labelId="import-sheet-label" value={sheetName} onChange={(event) => {
              setSheetName(event.target.value); setTargets({}); setKeyColumns([]); setParentColumn('')
            }}>
              {inspection.sheets.map((item) => <MenuItem key={item.name} value={item.name}>{item.name}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="import-entity-type-label">{t('imports.entityType')}</InputLabel>
            <Select label={t('imports.entityType')} labelId="import-entity-type-label" value={entityTypeId} onChange={(event) => {
              setEntityTypeId(event.target.value); setTargets({}); setKeyColumns([]); setParentColumn('')
            }}>
              {entityTypes.data?.items.map((item) => <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>)}
            </Select>
          </FormControl>
          <TextField label={t('imports.profileName')} value={profileName} onChange={(event) => setProfileName(event.target.value)} />
          {attributes.isFetching ? <CircularProgress aria-label={t('imports.loadingTargets')} size={24} /> : null}
          {columns.map((column) => (
            <FormControl fullWidth key={column.name}>
              <InputLabel id={`target-${column.name}`}>{`${column.name} ← ${t('imports.target')}`}</InputLabel>
              <Select label={`${column.name} ← ${t('imports.target')}`} labelId={`target-${column.name}`} value={targets[column.name] ?? ''} onChange={(event) => setTargets((current) => ({ ...current, [column.name]: event.target.value }))}>
                <MenuItem value="">{t('imports.skipColumn')}</MenuItem>
                <MenuItem value="system:name">{t('imports.systemName')}</MenuItem>
                <MenuItem value="system:description">{t('imports.systemDescription')}</MenuItem>
                <MenuItem value="system:parent_id">{t('imports.systemParent')}</MenuItem>
                {attributes.data?.filter((item) => !item.is_read_only).map((item) => (
                  <MenuItem key={item.id} value={`attribute:${item.id}`}>{item.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          ))}
          <FormControl fullWidth>
            <InputLabel id="matching-mode-label">{t('imports.matchingMode')}</InputLabel>
            <Select label={t('imports.matchingMode')} labelId="matching-mode-label" value={matchingMode} onChange={(event) => { setMatchingMode(event.target.value); setKeyColumns([]); setParentColumn('') }}>
              <MenuItem value="ENTITY_ID">{t('imports.matchEntityId')}</MenuItem>
              <MenuItem value="UNIQUE_ATTRIBUTE">{t('imports.matchUnique')}</MenuItem>
              <MenuItem value="COMPOSITE_KEY">{t('imports.matchComposite')}</MenuItem>
              <MenuItem value="PARENT_AND_KEY">{t('imports.matchParentKey')}</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel id="matching-columns-label">{t('imports.matchingColumns')}</InputLabel>
            <Select
              label={t('imports.matchingColumns')}
              labelId="matching-columns-label"
              multiple={matchingMode === 'COMPOSITE_KEY'}
              value={matchingMode === 'COMPOSITE_KEY' ? keyColumns : keyColumns[0] ?? ''}
              renderValue={(selected) => Array.isArray(selected) ? selected.join('، ') : selected}
              onChange={(event) => setKeyColumns(Array.isArray(event.target.value) ? event.target.value : [event.target.value])}
            >
              {columns.map((column) => <MenuItem key={column.name} value={column.name}><Checkbox checked={keyColumns.includes(column.name)} /><ListItemText primary={column.name} /></MenuItem>)}
            </Select>
          </FormControl>
          {matchingMode === 'PARENT_AND_KEY' ? (
            <FormControl fullWidth>
              <InputLabel id="parent-column-label">{t('imports.parentColumn')}</InputLabel>
              <Select label={t('imports.parentColumn')} labelId="parent-column-label" value={parentColumn} onChange={(event) => setParentColumn(event.target.value)}>
                {columns.map((column) => <MenuItem key={column.name} value={column.name}>{column.name}</MenuItem>)}
              </Select>
            </FormControl>
          ) : null}
          {!hasName && mappings.length > 0 ? <Alert severity="warning">{t('imports.nameRequired')}</Alert> : null}
          {!targetsAreDistinct ? <Alert severity="warning">{t('imports.duplicateTarget')}</Alert> : null}
          {!strategyValid && keyColumns.length > 0 ? <Alert severity="warning">{t('imports.invalidMatching')}</Alert> : null}
          {mutation.isError ? <Alert severity="error">{t('imports.profileSaveFailed')}</Alert> : null}
          <Button disabled={!canSave} onClick={() => mutation.mutate()} variant="contained">{t('imports.saveMapping')}</Button>
        </Stack>
      </CardContent>
    </Card>
  )
}
