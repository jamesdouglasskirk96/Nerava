import { test, expect } from '@playwright/test'

test.describe('Preferences Modal', () => {
  test.beforeEach(async ({ page }) => {
    // Clear session storage to ensure preferences modal shows
    await page.addInitScript(() => {
      sessionStorage.clear()
    })
    
    await page.goto('/m/mock_starbucks_001?mock=1&session_id=mock_session_12345')
    await expect(page.getByText('Starbucks Reserve')).toBeVisible({ timeout: 5000 })
  })

  test('should show preferences modal after first activation', async ({ page }) => {
    // Activate exclusive
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    
    // Wait for success modal
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    
    // Close success modal (View Wallet)
    page.on('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /View Wallet/i }).click()
    
    // Preferences modal should appear
    await expect(page.getByText('Want better matches next time?')).toBeVisible({ timeout: 2000 })
  })

  test('should show category checkboxes', async ({ page }) => {
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    
    page.on('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /View Wallet/i }).click()
    
    await expect(page.getByText('Want better matches next time?')).toBeVisible({ timeout: 2000 })
    
    // Check for category options
    await expect(page.getByText('Coffee')).toBeVisible()
    await expect(page.getByText('Food')).toBeVisible()
    await expect(page.getByText('Fitness')).toBeVisible()
  })

  test('should save preferences', async ({ page }) => {
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    
    page.on('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /View Wallet/i }).click()
    
    await expect(page.getByText('Want better matches next time?')).toBeVisible({ timeout: 2000 })
    
    // Select a category
    await page.getByText('Coffee').click()
    
    // Save
    await page.getByRole('button', { name: /Save Preferences/i }).click()
    
    // Modal should close
    await expect(page.getByText('Want better matches next time?')).not.toBeVisible({ timeout: 2000 })
  })

  test('should not show preferences modal on second activation', async ({ page }) => {
    // First activation
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    
    page.on('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /View Wallet/i }).click()
    
    // Close preferences modal
    await expect(page.getByText('Want better matches next time?')).toBeVisible({ timeout: 2000 })
    await page.getByRole('button', { name: /Save Preferences/i }).click()
    
    // Navigate to another merchant and activate
    await page.goto('/m/mock_tacos_001?mock=1&session_id=mock_session_12345')
    await expect(page.getByText('Taco Deli')).toBeVisible({ timeout: 5000 })
    
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    
    page.on('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /View Wallet/i }).click()
    
    // Preferences modal should NOT appear again
    await expect(page.getByText('Want better matches next time?')).not.toBeVisible({ timeout: 2000 })
  })
})

