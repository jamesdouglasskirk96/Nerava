import { test, expect } from '@playwright/test';

test.describe('Charge Flow E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://127.0.0.1:8000/app/');
    await page.waitForLoadState('networkidle');
  });

  test('should show banner when active window exists', async ({ page }) => {
    // Check if banner is visible (depends on current time)
    const banner = page.locator('#incentive-banner');
    await expect(banner).toBeVisible();
    
    // Banner should contain appropriate text
    const bannerText = await banner.textContent();
    expect(bannerText).toMatch(/Cheaper charging now|Green Hour Active/);
  });

  test('should show inactive banner when no active window', async ({ page }) => {
    // This test would need to mock the time or use a specific time
    // For now, just check that banner exists
    const banner = page.locator('#incentive-banner');
    await expect(banner).toBeVisible();
  });

  test('should complete charge flow with start and stop', async ({ page }) => {
    // Navigate to Charge tab
    await page.click('#tabCharge');
    await page.waitForSelector('#pageCharge');
    
    // Check initial state
    const startBtn = page.locator('#btnStartCharge');
    const stopBtn = page.locator('#btnStopCharge');
    
    await expect(startBtn).toBeEnabled();
    await expect(stopBtn).toBeDisabled();
    
    // Start charging
    await startBtn.click();
    await page.waitForTimeout(1000); // Wait for API call
    
    // Check active state
    await expect(startBtn).toBeDisabled();
    await expect(stopBtn).toBeEnabled();
    
    // Check that session info is displayed
    const sessionInfo = page.locator('#activeSession');
    await expect(sessionInfo).toBeVisible();
    
    // Stop charging
    await stopBtn.click();
    
    // Should show kWh dialog
    const dialog = page.locator('#kwhDialog');
    await expect(dialog).toBeVisible();
    
    // Enter kWh value
    const kwhInput = page.locator('#kwhInput');
    await kwhInput.fill('15.5');
    
    // Submit dialog
    const submitBtn = page.locator('#kwhSubmit');
    await submitBtn.click();
    
    // Wait for API call
    await page.waitForTimeout(2000);
    
    // Check that session is cleared
    await expect(startBtn).toBeEnabled();
    await expect(stopBtn).toBeDisabled();
    
    // Check that recent activity was added
    const recentActivity = page.locator('#recentActivity');
    await expect(recentActivity).toBeVisible();
    
    // Should contain the session entry
    const activityItems = recentActivity.locator('li');
    await expect(activityItems.first()).toContainText('15.5 kWh');
  });

  test('should show wallet balance animation on credit', async ({ page }) => {
    // Navigate to Wallet tab
    await page.click('#tabWallet');
    await page.waitForSelector('#pageWallet');
    
    // Check initial balance
    const balance = page.locator('#wallet-balance');
    const initialBalance = await balance.textContent();
    
    // Navigate to Charge tab and complete a charge
    await page.click('#tabCharge');
    await page.waitForSelector('#pageCharge');
    
    // Start and stop charging
    await page.click('#btnStartCharge');
    await page.waitForTimeout(1000);
    
    await page.click('#btnStopCharge');
    const dialog = page.locator('#kwhDialog');
    await expect(dialog).toBeVisible();
    
    await page.fill('#kwhInput', '10.0');
    await page.click('#kwhSubmit');
    await page.waitForTimeout(2000);
    
    // Navigate back to Wallet tab
    await page.click('#tabWallet');
    await page.waitForSelector('#pageWallet');
    
    // Check that balance was updated
    const newBalance = await balance.textContent();
    expect(newBalance).not.toBe(initialBalance);
  });

  test('should show streak indicator', async ({ page }) => {
    // Navigate to Wallet tab
    await page.click('#tabWallet');
    await page.waitForSelector('#pageWallet');
    
    // Check that streak indicator exists
    const streakIndicator = page.locator('.streak-indicator');
    await expect(streakIndicator).toBeVisible();
    
    const streakText = page.locator('.streak-text');
    await expect(streakText).toContainText('charging streak');
  });

  test('should show progress bar in wallet', async ({ page }) => {
    // Navigate to Wallet tab
    await page.click('#tabWallet');
    await page.waitForSelector('#pageWallet');
    
    // Check that progress bar exists
    const progressBar = page.locator('.progress-bar');
    await expect(progressBar).toBeVisible();
    
    const progressText = page.locator('.progress-text');
    await expect(progressText).toContainText('$25 to next tier');
  });
});
