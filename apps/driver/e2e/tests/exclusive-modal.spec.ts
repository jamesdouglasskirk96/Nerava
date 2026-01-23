import { test, expect } from '@playwright/test'

test.describe('Exclusive Activated Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/m/mock_starbucks_001?mock=1&session_id=mock_session_12345')
    await expect(page.getByText('Starbucks Reserve')).toBeVisible({ timeout: 5000 })
  })

  test('should show modal after activating exclusive', async ({ page }) => {
    // Click activate button
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    
    // Wait for modal
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    await expect(page.getByText(/Active for the next 60 minutes/i)).toBeVisible()
  })

  test('should show View Wallet button', async ({ page }) => {
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    await expect(page.getByRole('button', { name: /View Wallet/i })).toBeVisible()
  })

  test('should close modal when clicking View Wallet', async ({ page }) => {
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    
    // Click View Wallet (will show alert stub)
    page.on('dialog', dialog => dialog.accept())
    await page.getByRole('button', { name: /View Wallet/i }).click()
    
    // Modal should close
    await expect(page.getByText('Exclusive Activated')).not.toBeVisible({ timeout: 2000 })
  })

  test('should show merchant name and perk in modal', async ({ page }) => {
    await page.getByRole('button', { name: /Activate Exclusive/i }).click()
    
    await expect(page.getByText('Exclusive Activated')).toBeVisible({ timeout: 3000 })
    await expect(page.getByText('Starbucks Reserve')).toBeVisible()
  })
})

