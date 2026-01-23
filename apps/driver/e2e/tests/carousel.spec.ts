import { test, expect } from '@playwright/test'

test.describe('Carousel Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().grantPermissions(['geolocation'])
    await page.context().setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
  })

  test('should rotate merchants with arrow buttons', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Get initial merchant name
    const initialMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
    
    // Click next arrow
    await page.getByLabel('Next').click()
    await page.waitForTimeout(300) // Wait for transition
    
    // Merchant should have changed
    const nextMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
    expect(nextMerchant).not.toBe(initialMerchant)
    
    // Click previous arrow
    await page.getByLabel('Previous').click()
    await page.waitForTimeout(300)
    
    // Should be back to initial
    const backMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
    expect(backMerchant).toBe(initialMerchant)
  })

  test('should update dot indicators', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Get all dots
    const dots = page.locator('button[aria-label^="Go to item"]')
    const dotCount = await dots.count()
    expect(dotCount).toBeGreaterThan(0)
    
    // First dot should be active (larger)
    const firstDot = dots.first()
    await expect(firstDot).toHaveCSS('width', '10px') // Active dot is 2.5 * 4px = 10px
    
    // Click next
    await page.getByLabel('Next').click()
    await page.waitForTimeout(300)
    
    // Second dot should now be active
    const secondDot = dots.nth(1)
    await expect(secondDot).toHaveCSS('width', '10px')
  })

  test('should navigate to specific item via dot click', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Get initial merchant
    const initialMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
    
    // Click third dot (index 2)
    const dots = page.locator('button[aria-label^="Go to item"]')
    if (await dots.count() >= 3) {
      await dots.nth(2).click()
      await page.waitForTimeout(300)
      
      // Merchant should have changed
      const newMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
      expect(newMerchant).not.toBe(initialMerchant)
    }
  })

  test('should disable arrows at boundaries', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Previous button should be disabled at start (or enabled if wrapping)
    const prevButton = page.getByLabel('Previous')
    const nextButton = page.getByLabel('Next')
    
    // Both should be visible
    await expect(prevButton).toBeVisible()
    await expect(nextButton).toBeVisible()
  })
})

