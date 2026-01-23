import { test, expect } from '@playwright/test'

test.describe('Charging Flow E2E', () => {
  test('charging flow end-to-end', async ({ page, context }) => {
    // Set geolocation permission
    await context.grantPermissions(['geolocation'])
    
    // Set mock geolocation (Austin, TX - test coordinates)
    await context.setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
    
    // Navigate to While You Charge screen
    await page.goto('/wyc')
    
    // Wait for page to load and API call to complete
    await page.waitForLoadState('networkidle')
    
    // Assert featured merchant renders + has "Happy Hour ⭐️" badge
    await expect(page.getByText("You're Charging.")).toBeVisible()
    
    // Wait for merchants to load (MOCK_PLACES should return Asadas Grill and Eggman ATX)
    await expect(page.getByText(/Asadas Grill|Eggman ATX/)).toBeVisible({ timeout: 10000 })
    
    // Find featured merchant card (should be first/featured)
    const featuredMerchant = page.locator('text=Asadas Grill').first()
    await expect(featuredMerchant).toBeVisible()
    
    // Check for Happy Hour badge
    await expect(page.getByText('Happy Hour ⭐️')).toBeVisible()
    
    // Tap featured merchant → navigates to details page
    await featuredMerchant.click()
    
    // Wait for navigation to merchant details page
    await page.waitForURL(/\/m\//, { timeout: 5000 })
    
    // Assert merchant details page loaded
    await expect(page.getByText('Asadas Grill')).toBeVisible()
    
    // Tap "Add to Wallet"
    const addToWalletButton = page.getByRole('button', { name: /Add to Wallet/i })
    await expect(addToWalletButton).toBeVisible()
    await addToWalletButton.click()
    
    // Wait for API call
    await page.waitForTimeout(1000)
    
    // Assert success modal appears ("Added to Wallet")
    await expect(page.getByText('Added to Wallet')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/This pass is active while you're charging/i)).toBeVisible()
    
    // Tap "Done" closes modal
    const doneButton = page.getByRole('button', { name: /Done/i })
    await expect(doneButton).toBeVisible()
    await doneButton.click()
    
    // Modal should be closed
    await expect(page.getByText('Added to Wallet')).not.toBeVisible({ timeout: 2000 })
    
    // Should still be on merchant details page
    await expect(page.getByText('Asadas Grill')).toBeVisible()
  })
})




