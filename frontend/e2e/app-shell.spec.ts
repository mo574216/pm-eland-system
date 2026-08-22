import { expect, test } from '@playwright/test'

test('redirects an anonymous user from the protected workspace route', async ({ page }) => {
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({
        success: false,
        data: null,
        error: { code: 'AUTH_REQUIRED', message: 'نشست کاربری معتبر نیست.', details: {} },
        meta: {},
      }),
    })
  })
  await page.goto('/')

  await expect(page).toHaveURL(/\/login$/)
  await expect(page.locator('html')).toHaveAttribute('lang', 'fa')
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl')
  await expect(page.getByRole('heading', { name: 'ورود' })).toBeVisible()
  await expect(page.locator('body')).toHaveCSS('direction', 'rtl')
  expect(await page.locator('body').innerText()).not.toMatch(/[A-Za-z]/)
})

test('renders an enabled login form', async ({ page }) => {
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({ status: 401, contentType: 'application/json', body: '{}' })
  })
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: 'ورود' })).toBeVisible()
  await expect(page.getByLabel('نام کاربری')).toBeVisible()
  await expect(page.getByLabel('گذرواژه')).toBeVisible()
  await expect(page.getByRole('button', { name: 'ورود' })).toBeEnabled()
  expect(await page.locator('body').innerText()).not.toMatch(/[A-Za-z]/)
})

test('restores an authenticated session and lists accessible workspaces', async ({ page }) => {
  const userId = '38f186da-6259-420f-98ff-024055f42140'
  const workspaceId = '6ab93847-d2b3-43b8-aae1-15662031feb8'
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          access_token: 'test-access-token',
          token_type: 'bearer',
          expires_in: 900,
          user: {
            id: userId,
            username: 'analyst1',
            display_name: 'تحلیلگر',
            roles: ['ANALYST'],
          },
        },
        error: null,
        meta: {},
      }),
    })
  })
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          id: userId,
          username: 'analyst1',
          display_name: 'تحلیلگر',
          roles: ['ANALYST'],
          permissions: ['WORKSPACE_READ'],
          workspaces: [{ id: workspaceId, name: 'معماری سازمانی' }],
        },
        error: null,
        meta: {},
      }),
    })
  })
  await page.route('**/api/v1/workspaces?*', async (route) => {
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        data: {
          items: [
            {
              id: workspaceId,
              name: 'معماری سازمانی',
              slug: 'enterprise-architecture',
              description: 'فضای کاری نمونه',
              owner_id: userId,
              status: 'ACTIVE',
              configuration: {},
              created_at: '2026-08-22T00:00:00Z',
              updated_at: '2026-08-22T00:00:00Z',
              archived_at: null,
              version: 1,
            },
          ],
          page: 1,
          page_size: 200,
          total: 1,
        },
        error: null,
        meta: {},
      }),
    })
  })

  await page.goto('/')

  await expect(page).toHaveURL(/\/workspaces$/)
  await expect(page.getByRole('heading', { name: 'فضاهای کاری' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'معماری سازمانی' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'منوی کاربر' })).toBeVisible()
  await expect(page.getByLabel('انتخاب فضای کاری')).toBeVisible()
  expect(await page.locator('body').innerText()).not.toMatch(/[A-Za-z]/)
})
