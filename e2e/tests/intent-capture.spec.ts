import { test, expect } from '@playwright/test'

test.describe('Intent Capture E2E', () => {
  test('driver happy path with dev anon mode', async ({ page, context }) => {
    // Set geolocation permissions and coordinates
    await context.grantPermissions(['geolocation'])
    await context.setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
    
    // Navigate to /wyc (While You Charge page)
    await page.goto('/wyc')
    
    // Wait for merchants to load (MOCK_PLACES should return Asadas Grill, Eggman ATX)
    await expect(page.getByText("You're Charging.")).toBeVisible()
    await expect(page.getByText('Asadas Grill')).toBeVisible({ timeout: 5000 })
    
    // Assert featured merchant card renders
    const featuredCard = page.locator('[data-testid="featured-merchant"]')
    await expect(featuredCard).toBeVisible()
    
    // Assert 2 secondary merchants render
    const secondaryCards = page.locator('[data-testid="secondary-merchant"]')
    await expect(secondaryCards).toHaveCount(2)
    
    // Click featured merchant
    await featuredCard.click()
    
    // Assert navigation to merchant details
    await expect(page).toHaveURL(/\/m\/mock_asadas_grill/)
    
    // Click "Add to Wallet" button
    await page.getByRole('button', { name: /Add to Wallet/i }).click()
    
    // Assert "Added to Wallet" modal appears
    await expect(page.getByText(/Added to Wallet/i)).toBeVisible()
    
    // Click Done to close modal
    await page.getByRole('button', { name: /Done/i }).click()
    
    // Assert modal is closed
    await expect(page.getByText(/Added to Wallet/i)).not.toBeVisible()
  })
})







