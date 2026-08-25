import { Alert, Autocomplete, Button, CircularProgress, List, ListItem, ListItemText, Stack, TextField, Typography } from '@mui/material'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'

import { ApiError } from '../../api/client'
import {
  addWorkspaceMember,
  listWorkspaceRoleOptions,
  listWorkspaceMembers,
  removeWorkspaceMember,
  searchWorkspaceMemberOptions,
  type WorkspaceMemberCreate,
  type WorkspacePersonOption,
  type WorkspaceRoleOption,
} from './workspaceApi'

export function WorkspaceMemberManager({ workspaceId }: { workspaceId: string }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [mutationError, setMutationError] = useState<string | null>(null)
  const [personSearch, setPersonSearch] = useState('')
  const [selectedPerson, setSelectedPerson] = useState<WorkspacePersonOption | null>(null)
  const [selectedRole, setSelectedRole] = useState<WorkspaceRoleOption | null>(null)
  const members = useQuery({
    queryKey: ['workspace-members', workspaceId],
    queryFn: () => listWorkspaceMembers(workspaceId),
  })
  const people = useQuery({
    queryKey: ['workspace-member-options', workspaceId, personSearch],
    queryFn: () => searchWorkspaceMemberOptions(workspaceId, personSearch.trim()),
    enabled: personSearch.trim().length >= 2,
  })
  const roles = useQuery({
    queryKey: ['workspace-role-options', workspaceId],
    queryFn: () => listWorkspaceRoleOptions(workspaceId),
  })
  const addMember = useMutation({
    mutationFn: (values: WorkspaceMemberCreate) => addWorkspaceMember(workspaceId, values),
    onSuccess: async () => {
      setSelectedPerson(null)
      setSelectedRole(null)
      setPersonSearch('')
      await queryClient.invalidateQueries({ queryKey: ['workspace-members', workspaceId] })
    },
  })
  const removeMember = useMutation({
    mutationFn: (userId: string) => removeWorkspaceMember(workspaceId, userId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workspace-members', workspaceId] })
    },
  })

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setMutationError(null)
    if (selectedPerson === null || selectedRole === null) {
      setMutationError(t('workspaces.memberSelectionRequired'))
      return
    }
    try {
      await addMember.mutateAsync({ user_id: selectedPerson.id, role_id: selectedRole.id })
    } catch (error) {
      setMutationError(
        error instanceof ApiError && error.code === 'RESOURCE_CONFLICT'
          ? t('workspaces.memberExists')
          : t('workspaces.memberMutationFailed'),
      )
    }
  }

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
        <Autocomplete
          filterOptions={(options) => options}
          getOptionLabel={(option) => option.display_name ?? option.username}
          inputValue={personSearch}
          loading={people.isFetching}
          noOptionsText={personSearch.trim().length < 2 ? t('workspaces.searchPersonHelp') : t('workspaces.noPeopleFound')}
          onChange={(_, value) => setSelectedPerson(value)}
          onInputChange={(_, value) => setPersonSearch(value)}
          options={people.data ?? []}
          renderInput={(params) => <TextField {...params} label={t('workspaces.person')} />}
          value={selectedPerson}
        />
        <Autocomplete
          getOptionLabel={(option) => option.name}
          loading={roles.isFetching}
          onChange={(_, value) => setSelectedRole(value)}
          options={roles.data ?? []}
          renderInput={(params) => <TextField {...params} label={t('workspaces.role')} />}
          value={selectedRole}
        />
        <Button disabled={addMember.isPending} type="submit" variant="contained">
          {t('workspaces.addMember')}
        </Button>
      </Stack>
    </Stack>
  )
}
