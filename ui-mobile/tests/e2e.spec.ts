import { test, expect } from '@playwright/test';

test.describe('Nerava E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://127.0.0.1:8001/app/');
  });

  test('should load Explore page', async ({ page }) => {
    await expect(page.locator('#pageExplore')).toBeVisible();
    await expect(page.locator('#perkTitle')).toContainText('Starbucks');
  });

  test('should navigate between tabs', async ({ page }) => {
    // Test navigation
    await page.click('#tabCharge');
    await expect(page.locator('#pageCharge')).toBeVisible();
    
    await page.click('#tabWallet');
    await expect(page.locator('#pageWallet')).toBeVisible();
    
    await page.click('#tabMe');
    await expect(page.locator('#pageMe')).toBeVisible();
  });

  test('should show deal chip with countdown', async ({ page }) => {
    // Wait for deal chips to load
    await page.waitForSelector('.deal-chip', { timeout: 5000 });
    
    // Check deal chip contains expected text
    const dealChip = page.locator('.deal-chip').first();
    await expect(dealChip).toContainText('Green Hour — $');
    await expect(dealChip).toContainText('ends in');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/v1/hubs/recommended', route => route.abort());
    
    await page.reload();
    
    // Should still show fallback content
    await expect(page.locator('#perkTitle')).toBeVisible();
  });
});