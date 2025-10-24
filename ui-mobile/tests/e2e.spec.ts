import { test, expect } from '@playwright/test';

test.describe('Nerava App E2E Tests', () => {
  test.beforeAll(async ({ request }) => {
    // Ensure backend is running
    const response = await request.get('http://127.0.0.1:8001/health');
    expect(response.ok()).toBeTruthy();
  });

  test('demo banner appears when demo mode is enabled', async ({ page }) => {
    await page.goto('/');
    
    // Check for demo banner
    const demoBanner = page.locator('#demo-banner');
    await expect(demoBanner).toBeVisible();
    
    // Check banner content
    await expect(demoBanner.locator('.badge')).toHaveText('DEMO');
    await expect(demoBanner.locator('.state')).toBeVisible();
  });

  test('deal chips render with countdown', async ({ page }) => {
    await page.goto('/');
    
    // Wait for deal chips to load
    await page.waitForSelector('.deal-chips', { timeout: 5000 });
    
    // Check that deal chips are present
    const dealChips = page.locator('.deal-chip');
    await expect(dealChips).toHaveCount(3);
    
    // Check that countdown is updating
    const firstChip = dealChips.first();
    await expect(firstChip.locator('em')).toBeVisible();
  });

  test('map renders and scan panel hidden in demo', async ({ page }) => {
    await page.goto('/');
    await page.click('#tabCharge');
    
    // Check that map is visible
    await expect(page.locator('#chargeMap')).toBeVisible();
    
    // Check that scan panel is hidden in demo mode
    const scanPanel = page.locator('[data-role="scan-panel"]');
    if (await scanPanel.count() > 0) {
      await expect(scanPanel).toHaveCSS('display', 'none');
    }
  });

  test('wallet shows recent activity', async ({ page }) => {
    await page.goto('/');
    await page.click('#tabWallet');
    
    // Wait for wallet activity to load
    await page.waitForSelector('#wallet-activity', { timeout: 5000 });
    
    // Check that activity items are present
    const activityItems = page.locator('#wallet-activity li');
    await expect(activityItems).toHaveCount(5);
    
    // Check activity content
    const firstItem = activityItems.first();
    await expect(firstItem).toContainText('Verified charge');
  });

  test('EnergyRep score visible and modal opens', async ({ page }) => {
    await page.goto('/');
    await page.click('#tabMe');
    
    // Check that EnergyRep score is visible
    const repScore = page.locator('#repScore');
    await expect(repScore).toBeVisible();
    
    // Check that details button is present
    const detailsBtn = page.locator('button:has-text("View details")');
    await expect(detailsBtn).toBeVisible();
    
    // Click details button
    await detailsBtn.click();
    
    // Check that modal opens
    const modal = page.locator('dialog.modal');
    await expect(modal).toBeVisible();
    
    // Check modal content
    await expect(modal.locator('h3')).toHaveText('EnergyRep Breakdown');
    await expect(modal.locator('.breakdown-item')).toHaveCount(5);
  });

  test('dev tab accessible via keyboard shortcut', async ({ page }) => {
    await page.goto('/');
    
    // Press 'D' key to open dev tab
    await page.keyboard.press('KeyD');
    
    // Check that dev page is visible
    await expect(page.locator('#pageDev')).toBeVisible();
    
    // Check dev content
    const devContent = page.locator('#dev-content');
    await expect(devContent).toBeVisible();
  });

  test('dev tab shows Merchant Intel and Behavior Cloud views', async ({ page }) => {
    await page.goto('/#/dev');
    
    // Wait for dev content to load
    await page.waitForSelector('#dev-content', { timeout: 5000 });
    
    // Check that dev tabs are present
    const devTabs = page.locator('.dev-tabs button');
    await expect(devTabs).toHaveCount(2);
    
    // Click Merchant Intel tab
    await page.click('button[data-v="merchant"]');
    
    // Check that Merchant Intel view loads
    await expect(page.locator('h2')).toHaveText('Merchant Intelligence');
    await expect(page.locator('.grid')).toBeVisible();
    
    // Click Behavior Cloud tab
    await page.click('button[data-v="cloud"]');
    
    // Check that Behavior Cloud view loads
    await expect(page.locator('h2')).toHaveText('Behavior Cloud');
    await expect(page.locator('.grid')).toBeVisible();
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
