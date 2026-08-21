import { Button, Paper, Stack, TextField, Typography } from '@mui/material'

export function LoginPage() {
  return (
    <Stack sx={{ alignItems: 'center', justifyContent: 'center', minHeight: '100vh', p: 2 }}>
      <Paper component="main" elevation={2} sx={{ maxWidth: 420, p: 4, width: '100%' }}>
        <Stack component="form" spacing={3}>
          <Typography component="h1" variant="h1">
            Sign in
          </Typography>
          <TextField autoComplete="username" label="Email" name="email" required type="email" />
          <TextField
            autoComplete="current-password"
            label="Password"
            name="password"
            required
            type="password"
          />
          <Button disabled type="submit" variant="contained">
            Sign in
          </Button>
          <Typography color="text.secondary" variant="body2">
            Authentication will be enabled when the identity API is available.
          </Typography>
        </Stack>
      </Paper>
    </Stack>
  )
}
