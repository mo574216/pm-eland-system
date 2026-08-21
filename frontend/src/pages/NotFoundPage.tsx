import { Button, Stack, Typography } from '@mui/material'
import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <Stack component="main" spacing={2} sx={{ alignItems: 'center', p: 6 }}>
      <Typography component="h1" variant="h1">
        Page not found
      </Typography>
      <Button component={Link} to="/workspaces" variant="contained">
        Return to workspaces
      </Button>
    </Stack>
  )
}
