import { Alert, Stack, Typography } from '@mui/material'

export function WorkspaceListPage() {
  return (
    <Stack spacing={2}>
      <Typography component="h1" variant="h1">
        Workspaces
      </Typography>
      <Alert severity="info">
        Workspace data will appear here after the workspace API is implemented.
      </Alert>
    </Stack>
  )
}
