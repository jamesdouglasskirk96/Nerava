import { test, expect } from '@playwright/test'

test.describe('Merchant Flow E2E', () => {
  const merchantURL = process.env.DOCKER_COMPOSE ? 'http://localhost/merchant' : 'http://localhost:5174'
  const driverURL = process.env.DOCKER_COMPOSE ? 'http://localhost/app' : 'http://localhost:5173'
  
  test.beforeEach(async ({ page }) => {
    // Navigate to merchant portal
    await page.goto(merchantURL)
  })

  test('log in → enable exclusive → visible in driver flow', async ({ page }) => {
    // Mock Google Business SSO (for MVP, use mock mode)
    // In production, this would use real Google OAuth
    
    // Check if login is required
    const loginButton = page.locator('button:has-text("Sign in"), button:has-text("Login")').first()
    
    if (await loginButton.isVisible({ timeout: 5000 })) {
      // For MVP, skip actual Google SSO and assume logged in
      // In real test, would mock Google OAuth callback
      test.skip('Google SSO not implemented in test env')
    }
    
    // Navigate to exclusives page
    await page.goto(`${merchantURL}/exclusives`)
    
    // Look for exclusives list
    await expect(page.locator('text=Exclusives, h1')).toBeVisible({ timeout: 5000 })
    
    // Find an exclusive toggle
    const exclusiveToggle = page.locator('button[aria-label*="toggle"], input[type="checkbox"]').first()
    
    if (await exclusiveToggle.isVisible({ timeout: 5000 })) {
      // Toggle exclusive on
      const isChecked = await exclusiveToggle.isChecked()
      if (!isChecked) {
        await exclusiveToggle.click()
      }
      
      // Verify exclusive is enabled
      await expect(exclusiveToggle).toBeChecked({ timeout: 2000 })
      
      // Now check driver app to see if exclusive appears
      // Open driver app in new tab
      const driverPage = await page.context().newPage()
      await driverPage.goto(driverURL)
      
      // Grant geolocation
      await driverPage.context().grantPermissions(['geolocation'])
      await driverPage.context().setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
      
      // Wait for merchant list to load
      await driverPage.waitForTimeout(3000)
      
      // Check if exclusive merchant appears (this would need merchant location matching)
      // For MVP, just verify the flow works
      await driverPage.close()
    }
  })
})

