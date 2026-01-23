import { test, expect } from '@playwright/test'

test.describe('Charging State Screen', () => {
  test.beforeEach(async ({ page }) => {
    // Set geolocation permissions and coordinates
    await page.context().grantPermissions(['geolocation'])
    await page.context().setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
  })

  test('should render charging state screen with merchants', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    // Wait for merchants to load
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Here\'s what fits your charge.')).toBeVisible()
    
    // Assert featured merchant card renders
    const featuredCard = page.locator('[data-testid="featured-merchant"]')
    await expect(featuredCard).toBeVisible()
    
    // Assert 2 secondary merchants render
    const secondaryCards = page.locator('[data-testid="secondary-merchant"]')
    await expect(secondaryCards).toHaveCount(2)
  })

  test('should show carousel controls when multiple merchants', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Check for carousel controls (arrows and dots)
    const prevButton = page.getByLabel('Previous')
    const nextButton = page.getByLabel('Next')
    
    await expect(prevButton).toBeVisible()
    await expect(nextButton).toBeVisible()
  })

  test('should rotate merchants when clicking next', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Get first merchant name
    const firstMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
    
    // Click next
    await page.getByLabel('Next').click()
    
    // Wait for transition
    await page.waitForTimeout(300)
    
    // Merchant should have changed
    const secondMerchant = await page.locator('[data-testid="featured-merchant"] h3').first().textContent()
    expect(secondMerchant).not.toBe(firstMerchant)
  })

  test('should show category logo fallback when photo missing', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Check that placeholder is rendered (category logo)
    const placeholder = page.locator('[data-testid="featured-merchant"]').locator('svg')
    await expect(placeholder.first()).toBeVisible()
  })

  test('should navigate to merchant details on card click', async ({ page }) => {
    await page.goto('/wyc?mock=1')
    
    await expect(page.getByText("You're Charging.")).toBeVisible({ timeout: 5000 })
    
    // Click featured merchant
    await page.locator('[data-testid="featured-merchant"]').click()
    
    // Should navigate to merchant details
    await expect(page).toHaveURL(/\/m\/mock_starbucks_001/)
  })
})

