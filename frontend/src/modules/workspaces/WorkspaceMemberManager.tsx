import { Alert, Button, CircularProgress, List, ListItem, ListItemText, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { z } from 'zod'

import { ApiError } from '../../api/client'
import {
  addWorkspaceMember,
  listWorkspaceMembers,
  removeWorkspaceMember,
  type WorkspaceMemberCreate,
} from './workspaceApi'

const memberSchema = z.object({
  user_id: z.uuid(),
  role_id: z.uuid(),
})

export function WorkspaceMemberManager({ workspaceId }: { workspaceId: string }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [mutationError, setMutationError] = useState<string | null>(null)
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register,
    reset,
    setError,
  } = useForm<WorkspaceMemberCreate>()
  const members = useQuery({
    queryKey: ['workspace-members', workspaceId],
    queryFn: () => listWorkspaceMembers(workspaceId),
  })
  const addMember = useMutation({
    mutationFn: (values: WorkspaceMemberCreate) => addWorkspaceMember(workspaceId, values),
    onSuccess: async () => {
      reset()
      await queryClient.invalidateQueries({ queryKey: ['workspace-members', workspaceId] })
    },
  })
  const removeMember = useMutation({
    mutationFn: (userId: string) => removeWorkspaceMember(workspaceId, userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workspace-members', workspaceId] })
    },
  })

  const submit = handleSubmit(async (values) => {
    setMutationError(null)
    const parsed = memberSchema.safeParse(values)
    if (!parsed.success) {
      if (!z.uuid().safeParse(values.user_id).success) {
        setError('user_id', { message: t('workspaces.invalidUserId') })
      }
      if (!z.uuid().safeParse(values.role_id).success) {
        setError('role_id', { message: t('workspaces.invalidRoleId') })
      }
      return
    }
    try {
      await addMember.mutateAsync(parsed.data)
    } catch (error) {
      setMutationError(
        error instanceof ApiError && error.code === 'RESOURCE_CONFLICT'
          ? t('workspaces.memberExists')
          : t('workspaces.memberMutationFailed'),
      )
    }
  })

  const remove = async (userId: string) => {
    setMutationError(null)
    try {
      await removeMember.mutateAsync(userId)
    } catch {
      setMutationError(t('workspaces.memberMutationFailed'))
    }
  }

  return (
    <Stack spacing={2}>
      <Typography component="h2" variant="h5">
        {t('workspaces.members')}
      </Typography>
      {members.isPending ? <CircularProgress aria-label={t('workspaces.loadingMembers')} /> : null}
      {members.isError ? <Alert severity="error">{t('workspaces.membersLoadFailed')}</Alert> : null}
      {mutationError ? <Alert severity="error">{mutationError}</Alert> : null}
      <List>
        {members.data?.map((member) => (
          <ListItem
            key={member.id}
            secondaryAction={
              <Button
                color="error"
                disabled={removeMember.isPending}
                onClick={() => void remove(member.user_id)}
              >
                {t('workspaces.removeMember')}
              </Button>
            }
          >
            <ListItemText
              primary={member.display_name ?? member.username}
              secondary={member.role_code ?? t('workspaces.noRole')}
            />
          </ListItem>
        ))}
      </List>
      <Stack component="form" noValidate onSubmit={(event) => void submit(event)} spacing={2}>
        <Typography component="h3" variant="h6">
          {t('workspaces.addMember')}
        </Typography>
        <TextField
          error={errors.user_id !== undefined}
          helperText={errors.user_id?.message}
          label={t('workspaces.userId')}
          slotProps={{ htmlInput: { dir: 'ltr' } }}
          {...register('user_id')}
        />
        <TextField
          error={errors.role_id !== undefined}
          helperText={errors.role_id?.message}
          label={t('workspaces.roleId')}
          slotProps={{ htmlInput: { dir: 'ltr' } }}
          {...register('role_id')}
        />
        <Button disabled={isSubmitting} type="submit" variant="contained">
          {t('workspaces.addMember')}
        </Button>
      </Stack>
    </Stack>
  )
}
