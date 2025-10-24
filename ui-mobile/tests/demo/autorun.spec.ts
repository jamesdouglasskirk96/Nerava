import { test, expect } from '@playwright/test';

test.describe('Demo Autorun', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://127.0.0.1:8001/app/');
    await page.waitForLoadState('networkidle');
  });

  test('should start autorun with keyboard shortcut', async ({ page }) => {
    // Press Shift+R to start autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for autorun to start
    await page.waitForSelector('[data-demo-status="running"]', { timeout: 5000 });
    
    // Check that autorun is running
    const status = await page.textContent('[data-demo-status="running"]');
    expect(status).toContain('Demo autorun is running');
  });

  test('should show demo captions during autorun', async ({ page }) => {
    // Start autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for captions to appear
    await page.waitForSelector('.demo-caption', { timeout: 5000 });
    
    // Check caption content
    const caption = await page.textContent('.demo-caption');
    expect(caption).toBeTruthy();
    expect(caption.length).toBeGreaterThan(0);
  });

  test('should poll for backend updates', async ({ page }) => {
    // Start autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for poller to start
    await page.waitForSelector('[data-demo-poller="active"]', { timeout: 5000 });
    
    // Check that poller is active
    const pollerStatus = await page.getAttribute('[data-demo-poller="active"]', 'data-status');
    expect(pollerStatus).toBe('active');
  });

  test('should handle scenario changes', async ({ page }) => {
    // Start autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for autorun to start
    await page.waitForSelector('[data-demo-status="running"]', { timeout: 5000 });
    
    // Check that scenario can be changed
    const scenarioSelect = await page.locator('[data-demo-scenario]');
    if (await scenarioSelect.isVisible()) {
      await scenarioSelect.selectOption('peak_grid');
      
      // Wait for scenario change
      await page.waitForTimeout(1000);
      
      // Check that scenario changed
      const selectedScenario = await scenarioSelect.inputValue();
      expect(selectedScenario).toBe('peak_grid');
    }
  });

  test('should stop autorun on second Shift+R', async ({ page }) => {
    // Start autorun
    await page.keyboard.press('Shift+R');
    await page.waitForSelector('[data-demo-status="running"]', { timeout: 5000 });
    
    // Stop autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for autorun to stop
    await page.waitForSelector('[data-demo-status="stopped"]', { timeout: 5000 });
    
    // Check that autorun is stopped
    const status = await page.textContent('[data-demo-status="stopped"]');
    expect(status).toContain('Demo autorun stopped');
  });

  test('should show progress during execution', async ({ page }) => {
    // Start autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for progress indicator
    await page.waitForSelector('[data-demo-progress]', { timeout: 5000 });
    
    // Check progress content
    const progress = await page.textContent('[data-demo-progress]');
    expect(progress).toBeTruthy();
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/v1/demo/autorun/start', route => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });
    
    // Try to start autorun
    await page.keyboard.press('Shift+R');
    
    // Wait for error message
    await page.waitForSelector('[data-demo-error]', { timeout: 5000 });
    
    // Check error message
    const error = await page.textContent('[data-demo-error]');
    expect(error).toContain('Failed to start demo autorun');
  });
});
