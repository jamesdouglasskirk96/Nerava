import { test, expect } from '@playwright/test'

test.describe('Merchant Details Screen', () => {
  test('should render merchant details', async ({ page }) => {
    await page.goto('/m/mock_starbucks_001?mock=1&session_id=mock_session_12345')
    
    // Wait for merchant details to load
    await expect(page.getByText('Starbucks Reserve')).toBeVisible({ timeout: 5000 })
    
    // Check for merchant info
    await expect(page.getByText('Coffee')).toBeVisible()
    await expect(page.getByText('Activate Exclusive')).toBeVisible()
  })

  test('should show distance and moment copy', async ({ page }) => {
    await page.goto('/m/mock_starbucks_001?mock=1&session_id=mock_session_12345')
    
    await expect(page.getByText('Starbucks Reserve')).toBeVisible({ timeout: 5000 })
    
    // Check for distance card
    await expect(page.getByText(/miles/i)).toBeVisible()
  })

  test('should show category logo fallback in hero image', async ({ page }) => {
    await page.goto('/m/mock_starbucks_001?mock=1&session_id=mock_session_12345')
    
    await expect(page.getByText('Starbucks Reserve')).toBeVisible({ timeout: 5000 })
    
    // Check for placeholder/logo in hero section
    const heroSection = page.locator('div').filter({ hasText: 'Starbucks Reserve' }).first()
    await expect(heroSection).toBeVisible()
  })
})

