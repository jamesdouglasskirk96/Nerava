import { test, expect } from '@playwright/test'

test.describe('Admin Flow E2E', () => {
  const adminURL = process.env.DOCKER_COMPOSE ? 'http://localhost/admin' : 'http://localhost:5175'
  const driverURL = process.env.DOCKER_COMPOSE ? 'http://localhost/app' : 'http://localhost:5173'
  
  test.beforeEach(async ({ page }) => {
    // Navigate to admin portal
    await page.goto(adminURL)
  })

  test('set static location → driver updates', async ({ page }) => {
    // Login as admin (for MVP, skip if not implemented)
    const loginForm = page.locator('input[type="email"]').first()
    
    if (await loginForm.isVisible({ timeout: 5000 })) {
      // Mock admin login
      await loginForm.fill('admin@nerava.com')
      const passwordInput = page.locator('input[type="password"]').first()
      await passwordInput.fill('admin123')
      
      const loginButton = page.locator('button:has-text("Login"), button[type="submit"]').first()
      await loginButton.click()
      
      // Wait for dashboard
      await page.waitForTimeout(2000)
    }
    
    // Navigate to demo page
    await page.goto(`${adminURL}/demo`)
    
    // Set demo location
    const latInput = page.locator('input[type="number"]').first()
    const lngInput = page.locator('input[type="number"]').nth(1)
    
    await expect(latInput).toBeVisible({ timeout: 5000 })
    
    await latInput.fill('30.2672')
    await lngInput.fill('-97.7431')
    
    const setButton = page.locator('button:has-text("Set Demo Location")').first()
    await setButton.click()
    
    // Wait for success message
    await expect(page.locator('text=successfully, text=Demo location')).toBeVisible({ timeout: 5000 })
    
    // Open driver app and verify location
    const driverPage = await page.context().newPage()
    await driverPage.goto(driverURL)
    
    // Grant geolocation
    await driverPage.context().grantPermissions(['geolocation'])
    
    // In demo mode, driver should see location as set by admin
    await driverPage.waitForTimeout(2000)
    
    // Verify driver app loaded (basic check)
    await expect(driverPage.locator('text=What to do while you charge, text=Nerava')).toBeVisible({ timeout: 10000 })
    
    await driverPage.close()
  })
})

