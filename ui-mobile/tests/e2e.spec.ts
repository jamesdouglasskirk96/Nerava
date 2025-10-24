import { test, expect } from '@playwright/test';

test.describe('Nerava App E2E Tests', () => {
  test.beforeAll(async ({ request }) => {
    // Ensure backend is running
    const response = await request.get('http://127.0.0.1:8001/health');
    expect(response.ok()).toBeTruthy();
  });

  test('loads Explore page with map and perk card', async ({ page }) => {
    await page.goto('/');
    
    // Wait for map to load
    await page.waitForSelector('#mapContainer', { timeout: 10000 });
    
    // Check that perk card is visible
    await expect(page.locator('#explorePerkSheet')).toBeVisible();
    
    // Check that "View more" button exists and click it
    const viewMoreBtn = page.locator('text=View more');
    await expect(viewMoreBtn).toBeVisible();
    await viewMoreBtn.click();
    
    // Should navigate to Claim tab
    await expect(page.locator('#pageClaim')).toBeVisible();
  });

  test('navigates between tabs', async ({ page }) => {
    await page.goto('/');
    
    // Test Explore -> Charge
    await page.click('#tabCharge');
    await expect(page.locator('#pageCharge')).toBeVisible();
    
    // Test Charge -> Wallet
    await page.click('#tabWallet');
    await expect(page.locator('#pageWallet')).toBeVisible();
    
    // Test Wallet -> Me
    await page.click('#tabMe');
    await expect(page.locator('#pageMe')).toBeVisible();
    
    // Test Me -> Explore
    await page.click('#tabExplore');
    await expect(page.locator('#pageExplore')).toBeVisible();
  });

  test('social flow with backend integration', async ({ page, request }) => {
    // Setup: Create follow relationship and award
    await request.post('http://127.0.0.1:8001/v1/social/follow', {
      data: { follower_id: 'testuser1', followee_id: 'testuser2', follow: true }
    });
    
    await request.post('http://127.0.0.1:8001/v1/incentives/award', {
      params: { user_id: 'testuser2', cents: 250 }
    });
    
    await request.post('http://127.0.0.1:8001/v1/admin/settle');
    
    // Navigate to Charge page
    await page.goto('/');
    await page.click('#tabCharge');
    
    // Wait for feed to load
    await page.waitForSelector('#chargeFeedList', { timeout: 5000 });
    
    // Check that feed shows the activity
    const feedContent = await page.textContent('#chargeFeedList');
    expect(feedContent).toContain('testuser2');
    expect(feedContent).toContain('$2.50');
  });

  test('wallet page loads correctly', async ({ page }) => {
    await page.goto('/');
    await page.click('#tabWallet');
    
    // Check wallet elements are present
    await expect(page.locator('#pageWallet')).toBeVisible();
    
    // Check for wallet progress indicator
    const walletProgress = page.locator('#walletProgress');
    if (await walletProgress.count() > 0) {
      await expect(walletProgress).toBeVisible();
    }
  });

  test('me page loads correctly', async ({ page }) => {
    await page.goto('/');
    await page.click('#tabMe');
    
    // Check me page elements
    await expect(page.locator('#pageMe')).toBeVisible();
    
    // Check for profile elements
    const profileElements = page.locator('.profile, .settings, .account');
    if (await profileElements.count() > 0) {
      await expect(profileElements.first()).toBeVisible();
    }
  });
});
