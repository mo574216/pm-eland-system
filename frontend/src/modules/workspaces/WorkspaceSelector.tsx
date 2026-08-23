import { FormControl, InputLabel, MenuItem, Select } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'

import type { AppDispatch, RootState } from '../../store/store'
import { workspaceSelected } from '../../store/store'
import { listWorkspaces } from './workspaceApi'

export function WorkspaceSelector() {
  const { t } = useTranslation()
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const selectedWorkspaceId = useSelector((state: RootState) => state.ui.selectedWorkspaceId)
  const workspaces = useQuery({ queryKey: ['workspaces'], queryFn: listWorkspaces })

  if (!workspaces.data?.items.length) {
    return null
  }

  return (
    <FormControl size="small" sx={{ bgcolor: 'background.paper', minWidth: 220 }}>
      <InputLabel id="workspace-selector-label">{t('workspaces.selector')}</InputLabel>
      <Select
        label={t('workspaces.selector')}
        labelId="workspace-selector-label"
        onChange={(event) => {
          const workspaceId = event.target.value
          dispatch(workspaceSelected(workspaceId))
          void navigate(`/workspaces/${workspaceId}/entities`)
        }}
        value={selectedWorkspaceId ?? ''}
      >
        {workspaces.data.items.map((workspace) => (
          <MenuItem key={workspace.id} value={workspace.id}>
            {workspace.name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}
