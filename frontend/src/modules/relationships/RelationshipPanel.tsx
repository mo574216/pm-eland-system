import DeleteIcon from '@mui/icons-material/Delete'
import {
  Alert,
  Autocomplete,
  Button,
  Card,
  CardActions,
  CardContent,
  CircularProgress,
  IconButton,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '../../api/client'
import { listEntities } from '../entities/entityApi'
import {
  createRelationship,
  deleteRelationship,
  listRelationships,
  listRelationshipTypes,
} from './relationshipApi'

interface RelationshipPanelProps {
  canManage: boolean
  entityId: string
  workspaceId: string
}

export function RelationshipPanel({ canManage, entityId, workspaceId }: RelationshipPanelProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [relationshipTypeId, setRelationshipTypeId] = useState<string | null>(null)
  const [targetEntityId, setTargetEntityId] = useState<string | null>(null)
  const [mutationError, setMutationError] = useState<string | null>(null)
  const relationships = useQuery({
    queryKey: ['relationships', entityId],
    queryFn: () => listRelationships(entityId),
  })
  const relationshipTypes = useQuery({
    queryKey: ['relationship-types', workspaceId],
    queryFn: () => listRelationshipTypes(workspaceId),
  })
  const entities = useQuery({
    queryKey: ['entities', workspaceId, 'relationship-options'],
    queryFn: () => listEntities(workspaceId),
  })
  const create = useMutation({
    mutationFn: () => {
      if (relationshipTypeId === null || targetEntityId === null) {
        throw new Error('Relationship selection is incomplete.')
      }
      return createRelationship(workspaceId, {
        relationship_type_id: relationshipTypeId,
        source_entity_id: entityId,
        target_entity_id: targetEntityId,
      })
    },
    onSuccess: async () => {
      setTargetEntityId('')
      await queryClient.invalidateQueries({ queryKey: ['relationships', entityId] })
    },
  })
  const remove = useMutation({
    mutationFn: (relationshipId: string) => deleteRelationship(relationshipId),
    onSuccess: async () =>
      queryClient.invalidateQueries({ queryKey: ['relationships', entityId] }),
  })

  const typeById = new Map(
    relationshipTypes.data?.items.map((type) => [type.id, type]) ?? [],
  )
  const entityById = new Map(entities.data?.items.map((entity) => [entity.id, entity]) ?? [])
  const currentEntity = entityById.get(entityId)
  const compatibleTypes = relationshipTypes.data?.items.filter(
    (type) => type.source_type_id === null || type.source_type_id === currentEntity?.entity_type_id,
  ) ?? []
  const selectedType = compatibleTypes.find((type) => type.id === relationshipTypeId) ?? null
  const availableTargets = entities.data?.items.filter(
    (entity) => entity.id !== entityId
      && (selectedType?.target_type_id === null
        || selectedType?.target_type_id === undefined
        || entity.entity_type_id === selectedType.target_type_id),
  ) ?? []
  const selectedTarget = availableTargets.find((entity) => entity.id === targetEntityId) ?? null

  const submit = async () => {
    setMutationError(null)
    try {
      await create.mutateAsync()
    } catch (error) {
      setMutationError(
        error instanceof ApiError && error.code === 'INVALID_RELATIONSHIP'
          ? t('relationships.invalid')
          : t('relationships.saveFailed'),
      )
    }
  }

  return (
    <Stack spacing={2}>
      <Typography component="h2" variant="h5">{t('entities.tabs.relationships')}</Typography>
      {canManage ? (
        <Stack spacing={2}>
          <Typography color="text.secondary">{t('relationships.createHelp')}</Typography>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ alignItems: 'center' }}>
          <Typography sx={{ minWidth: 120 }}>{currentEntity?.name ?? t('relationships.currentItem')}</Typography>
          <Autocomplete
            getOptionLabel={(option) => option.name}
            onChange={(_, value) => {
              setRelationshipTypeId(value?.id ?? null)
              setTargetEntityId(null)
            }}
            options={compatibleTypes}
            renderInput={(params) => <TextField {...params} label={t('relationships.action')} />}
            sx={{ minWidth: 220 }}
            value={selectedType}
          />
          <Autocomplete
            disabled={selectedType === null}
            getOptionLabel={(option) => `${option.name} — ${option.entity_type.name}`}
            onChange={(_, value) => setTargetEntityId(value?.id ?? null)}
            options={availableTargets}
            renderInput={(params) => <TextField {...params} label={t('relationships.relatedItem')} />}
            sx={{ minWidth: 280 }}
            value={selectedTarget}
          />
          <Button
            disabled={!relationshipTypeId || !targetEntityId || create.isPending}
            onClick={() => void submit()}
            variant="contained"
          >
            {t('relationships.create')}
          </Button>
          </Stack>
        </Stack>
      ) : null}
      {mutationError ? <Alert severity="error">{mutationError}</Alert> : null}
      {relationships.isPending || relationshipTypes.isPending || entities.isPending ? (
        <CircularProgress aria-label={t('relationships.loading')} />
      ) : null}
      {relationships.isError || relationshipTypes.isError || entities.isError ? (
        <Alert severity="error">{t('relationships.loadFailed')}</Alert>
      ) : null}
      {relationships.data?.items.length === 0 ? (
        <Alert severity="info">{t('relationships.empty')}</Alert>
      ) : null}
      {relationships.data?.items.map((relationship) => {
        const outgoing = relationship.source_entity_id === entityId
        const counterpartId = outgoing
          ? relationship.target_entity_id
          : relationship.source_entity_id
        return (
          <Card key={relationship.id} variant="outlined">
            <CardContent>
              <Typography component="h3" variant="h6">
                {outgoing ? currentEntity?.name : entityById.get(counterpartId)?.name}
                {' '}
                {typeById.get(relationship.relationship_type_id)?.name ?? t('relationships.relatedTo')}
                {' '}
                {outgoing ? entityById.get(counterpartId)?.name : currentEntity?.name}
              </Typography>
            </CardContent>
            {canManage ? (
              <CardActions>
                <IconButton
                  aria-label={t('relationships.delete')}
                  disabled={remove.isPending}
                  onClick={() => void remove.mutateAsync(relationship.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            ) : null}
          </Card>
        )
      })}
    </Stack>
  )
}
