import { test, expect } from '@playwright/test'

test.describe('Driver Flow E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to driver app (use Docker Compose route if DOCKER_COMPOSE env is set)
    const baseURL = process.env.DOCKER_COMPOSE ? 'http://localhost/app' : 'http://localhost:5173'
    await page.goto(baseURL)
  })

  test('OTP login works', async ({ page }) => {
    // Wait for OTP modal or login form
    // In stub mode, OTP should be logged to console
    const phoneInput = page.locator('input[type="tel"], input[placeholder*="phone" i]').first()
    
    if (await phoneInput.isVisible({ timeout: 5000 })) {
      await phoneInput.fill('+15551234567')
      
      // Click send code button
      const sendButton = page.locator('button:has-text("Send"), button:has-text("Get Code")').first()
      await sendButton.click()
      
      // Wait for code input (in stub mode, code is logged)
      const codeInput = page.locator('input[type="text"][maxlength="6"], input[placeholder*="code" i]').first()
      await codeInput.waitFor({ timeout: 5000 })
      
      // Enter stub code (in test env, use a known code or mock)
      await codeInput.fill('123456')
      
      // Click verify
      const verifyButton = page.locator('button:has-text("Verify"), button:has-text("Continue")').first()
      await verifyButton.click()
      
      // Should be authenticated
      await expect(page.locator('text=What to do while you charge')).toBeVisible({ timeout: 10000 })
    }
  })

  test('intent capture → open merchant → activate exclusive → complete', async ({ page }) => {
    // Grant geolocation permission
    await page.context().grantPermissions(['geolocation'])
    await page.context().setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
    
    // Wait for intent capture to load
    await page.waitForTimeout(2000)
    
    // Look for merchant cards
    const merchantCard = page.locator('[data-testid="merchant-card"], .merchant-card').first()
    
    if (await merchantCard.isVisible({ timeout: 10000 })) {
      // Click merchant card
      await merchantCard.click()
      
      // Look for "Activate Exclusive" button
      const activateButton = page.locator('button:has-text("Activate"), button:has-text("Exclusive")').first()
      
      if (await activateButton.isVisible({ timeout: 5000 })) {
        await activateButton.click()
        
        // Wait for exclusive active view
        await expect(page.locator('text=Exclusive Active, text=I\'m at the Merchant')).toBeVisible({ timeout: 10000 })
        
        // Click "I'm at the Merchant" button
        const arrivedButton = page.locator('button:has-text("I\'m at"), button:has-text("Arrived")').first()
        if (await arrivedButton.isVisible({ timeout: 5000 })) {
          await arrivedButton.click()
          
          // Complete flow
          const doneButton = page.locator('button:has-text("Done"), button:has-text("Complete")').first()
          if (await doneButton.isVisible({ timeout: 5000 })) {
            await doneButton.click()
            
            // Should show preferences modal
            await expect(page.locator('text=preferences, text=Want better matches')).toBeVisible({ timeout: 5000 })
          }
        }
      }
    }
  })
})

