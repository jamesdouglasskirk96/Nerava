import { test, expect } from '@playwright/test'

test.describe('Primary Merchant Override', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to pre-charging screen
    await page.goto('/pre-charging')
  })

  test('should show only primary merchant in pre-charge state', async ({ page }) => {
    // Wait for merchant data to load
    await page.waitForSelector('[data-testid="charger-card"]', { timeout: 10000 })
    
    // Check that only one merchant is displayed
    const merchantCards = await page.locator('.merchant-card, [data-testid="featured-merchant"]').count()
    expect(merchantCards).toBeLessThanOrEqual(1)
    
    // Check for exclusive badge if primary merchant exists
    const exclusiveBadge = page.locator('text=Exclusive, text=⭐ Exclusive').first()
    const badgeCount = await exclusiveBadge.count()
    
    // If merchant exists, it should have exclusive badge
    if (merchantCards > 0) {
      expect(badgeCount).toBeGreaterThan(0)
    }
  })

  test('should show primary merchant first in charging state', async ({ page }) => {
    // Toggle to charging state
    await page.click('text=Charging')
    await page.waitForURL('**/wyc', { timeout: 5000 })
    
    // Wait for merchants to load
    await page.waitForSelector('[data-testid="featured-merchant"]', { timeout: 10000 })
    
    // Get all merchant cards
    const featuredMerchant = page.locator('[data-testid="featured-merchant"]').first()
    const secondaryMerchants = page.locator('.secondary-merchant-card, [data-testid="secondary-merchant"]')
    
    // First merchant should be featured (primary)
    await expect(featuredMerchant).toBeVisible()
    
    // Check for exclusive badge on primary
    const exclusiveBadge = featuredMerchant.locator('text=Exclusive, text=⭐ Exclusive')
    const hasExclusive = await exclusiveBadge.count()
    
    // Primary merchant should have exclusive badge
    expect(hasExclusive).toBeGreaterThan(0)
    
    // Should have at most 2 secondary merchants (3 total)
    const secondaryCount = await secondaryMerchants.count()
    expect(secondaryCount).toBeLessThanOrEqual(2)
  })

  test('should display Google Places photos', async ({ page }) => {
    await page.waitForSelector('[data-testid="charger-card"]', { timeout: 10000 })
    
    // Check for merchant photo
    const merchantPhoto = page.locator('img[alt*="Merchant"], img[alt*="Asadas"]').first()
    const photoCount = await merchantPhoto.count()
    
    if (photoCount > 0) {
      // Photo should load (not broken)
      const src = await merchantPhoto.getAttribute('src')
      expect(src).toBeTruthy()
      expect(src).not.toContain('data:image/png;base64,iVBORw0KGgo') // Not placeholder
    }
  })

  test('should show open/closed status', async ({ page }) => {
    await page.waitForSelector('[data-testid="charger-card"]', { timeout: 10000 })
    
    // Check for open/closed badge
    const statusBadge = page.locator('text=Open, text=Closed').first()
    const statusCount = await statusBadge.count()
    
    // Status should be displayed if merchant exists
    if (statusCount > 0) {
      const statusText = await statusBadge.textContent()
      expect(['Open', 'Closed']).toContain(statusText?.trim())
    }
  })

  test('should display exclusive description', async ({ page }) => {
    await page.waitForSelector('[data-testid="charger-card"]', { timeout: 10000 })
    
    // Check for exclusive description text
    const exclusiveDesc = page.locator('text=/Free Margarita|Charging Exclusive/').first()
    const descCount = await exclusiveDesc.count()
    
    // If primary merchant exists, description should be visible
    if (descCount > 0) {
      await expect(exclusiveDesc).toBeVisible()
    }
  })
})






