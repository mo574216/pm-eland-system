import { expect, test } from '@playwright/test'

test('renders the application shell and workspace route', async ({ page }) => {
  await page.goto('/')

  await expect(page).toHaveURL(/\/workspaces$/)
  await expect(page.locator('html')).toHaveAttribute('lang', 'fa')
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl')
  await expect(page.getByRole('heading', { name: 'فضاهای کاری' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'منوی کاربر' })).toBeVisible()
  await expect(page.locator('body')).toHaveCSS('direction', 'rtl')
  expect(await page.locator('body').innerText()).not.toMatch(/[A-Za-z]/)
})

test('renders the placeholder login route', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: 'ورود' })).toBeVisible()
  await expect(page.getByLabel('ایمیل')).toBeVisible()
  await expect(page.getByLabel('گذرواژه')).toBeVisible()
  await expect(page.getByRole('button', { name: 'ورود' })).toBeDisabled()
  expect(await page.locator('body').innerText()).not.toMatch(/[A-Za-z]/)
})
