import { test, expect } from '@playwright/test'

test.describe('Pre-Charging State Screen', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().grantPermissions(['geolocation'])
    await page.context().setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
  })

  test('should render pre-charging state screen with chargers', async ({ page }) => {
    await page.goto('/pre-charging?mock=1')
    
    // Wait for screen to load
    await expect(page.getByText('Find a charger near experiences')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Discover charging stations with great places nearby')).toBeVisible()
    
    // Check for charger card
    const chargerCard = page.locator('[data-testid="charger-card"]')
    await expect(chargerCard).toBeVisible()
  })

  test('should show charger details', async ({ page }) => {
    await page.goto('/pre-charging?mock=1')
    
    await expect(page.getByText('Find a charger near experiences')).toBeVisible({ timeout: 5000 })
    
    // Check for charger information
    await expect(page.getByText(/stalls/i)).toBeVisible()
    await expect(page.getByText(/Navigate to Charger/i)).toBeVisible()
  })

  test('should show nearby experiences in charger card', async ({ page }) => {
    await page.goto('/pre-charging?mock=1')
    
    await expect(page.getByText('Find a charger near experiences')).toBeVisible({ timeout: 5000 })
    
    // Check for nearby experiences section
    await expect(page.getByText('Nearby experiences')).toBeVisible()
  })

  test('should show pre-charging pill in header', async ({ page }) => {
    await page.goto('/pre-charging?mock=1')
    
    await expect(page.getByText('Pre-Charging')).toBeVisible({ timeout: 5000 })
  })
})

