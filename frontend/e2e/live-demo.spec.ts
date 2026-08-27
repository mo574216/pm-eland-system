import { expect, test } from '@playwright/test'

const username = process.env.LIVE_DEMO_USERNAME
const password = process.env.LIVE_DEMO_PASSWORD

test.describe('live MVP demo', () => {
  test.skip(!username || !password, 'Set runtime-only LIVE_DEMO_USERNAME and LIVE_DEMO_PASSWORD.')

  test('shows the staged governed deliverable in the right-side workspace shell', async ({ page }) => {
    await page.goto('/login')
    await page.locator('input[autocomplete="username"]').fill(username ?? '')
    await page.locator('input[autocomplete="current-password"]').fill(password ?? '')
    await page.locator('button[type="submit"]').click()

    await expect(page).toHaveURL(/\/workspaces$/)
    await page.getByRole('button', { name: 'باز کردن' }).click()
    await expect(page).toHaveURL(/\/workspaces\/[^/]+$/)

    await page.getByRole('link', { name: 'مراحل پروژه' }).click()
    await expect(page).toHaveURL(/\/phases$/)
    await expect(page.getByRole('heading', { name: 'مرحله نمونه تحویل‌دادنی' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'کارپوشه مشخصات فرایند نمونه' })).toBeVisible()

    const drawerBounds = await page.locator('.MuiDrawer-paper').boundingBox()
    const viewportWidth = page.viewportSize()?.width ?? 0
    expect(drawerBounds).not.toBeNull()
    expect(drawerBounds?.x ?? 0).toBeGreaterThan(viewportWidth / 2)
  })
})
