import { expect, test } from '@playwright/test'

test('renders the application shell and workspace route', async ({ page }) => {
  await page.goto('/')

  await expect(page).toHaveURL(/\/workspaces$/)
  await expect(page.getByRole('heading', { name: 'Workspaces' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'User menu' })).toBeVisible()
})

test('renders the placeholder login route', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeDisabled()
})
