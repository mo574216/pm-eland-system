import DeleteIcon from '@mui/icons-material/Delete'
import {
  Alert,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
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
  const [relationshipTypeId, setRelationshipTypeId] = useState('')
  const [targetEntityId, setTargetEntityId] = useState('')
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
    mutationFn: () =>
      createRelationship(workspaceId, {
        relationship_type_id: relationshipTypeId,
        source_entity_id: entityId,
        target_entity_id: targetEntityId,
      }),
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
  const availableTargets = entities.data?.items.filter((entity) => entity.id !== entityId) ?? []

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
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ alignItems: 'stretch' }}>
          <FormControl sx={{ minWidth: 180 }}>
            <InputLabel id="relationship-type-label">{t('relationships.type')}</InputLabel>
            <Select
              label={t('relationships.type')}
              labelId="relationship-type-label"
              onChange={(event) => setRelationshipTypeId(event.target.value)}
              value={relationshipTypeId}
            >
              {relationshipTypes.data?.items.map((type) => (
                <MenuItem key={type.id} value={type.id}>{type.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 220 }}>
            <InputLabel id="relationship-target-label">{t('relationships.target')}</InputLabel>
            <Select
              label={t('relationships.target')}
              labelId="relationship-target-label"
              onChange={(event) => setTargetEntityId(event.target.value)}
              value={targetEntityId}
            >
              {availableTargets.map((entity) => (
                <MenuItem key={entity.id} value={entity.id}>{entity.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            disabled={!relationshipTypeId || !targetEntityId || create.isPending}
            onClick={() => void submit()}
            variant="contained"
          >
            {t('relationships.create')}
          </Button>
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
              <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                <Typography component="h3" variant="h6">
                  {typeById.get(relationship.relationship_type_id)?.name ??
                    relationship.relationship_type_id}
                </Typography>
                <Chip
                  label={t(`relationships.direction.${outgoing ? 'outgoing' : 'incoming'}`)}
                  size="small"
                  variant="outlined"
                />
              </Stack>
              <Typography>{entityById.get(counterpartId)?.name ?? counterpartId}</Typography>
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
