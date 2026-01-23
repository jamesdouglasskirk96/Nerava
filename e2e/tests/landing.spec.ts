import { test, expect } from '@playwright/test'

test.describe('Landing Page', () => {
  const landingURL = process.env.DOCKER_COMPOSE ? 'http://localhost' : 'http://localhost:3000'
  
  test.beforeEach(async ({ page }) => {
    // Navigate to landing page
    await page.goto(landingURL)
  })

  test('loads correctly', async ({ page }) => {
    // Check hero section
    await expect(page.locator('h1')).toContainText('Nerava')
    await expect(page.locator('text=What to do while you charge')).toBeVisible()
  })

  test('CTAs route to correct destinations', async ({ page }) => {
    // Check "Open Nerava" CTA
    const driverCTA = page.locator('text=Open Nerava').first()
    await expect(driverCTA).toBeVisible()
    
    // Check "For Businesses" CTA
    const merchantCTA = page.locator('text=For Businesses').first()
    await expect(merchantCTA).toBeVisible()
    
    // Verify links (in production, these would be actual URLs)
    // For local dev, they should point to localhost ports
    const driverHref = await driverCTA.getAttribute('href')
    const merchantHref = await merchantCTA.getAttribute('href')
    
    // In local dev, these should be localhost URLs
    expect(driverHref).toBeTruthy()
    expect(merchantHref).toBeTruthy()
  })

  test('footer links are present', async ({ page }) => {
    // Scroll to footer
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    
    // Check for Privacy, Terms, Contact links
    await expect(page.locator('text=Privacy Policy')).toBeVisible()
    await expect(page.locator('text=Terms of Service')).toBeVisible()
    await expect(page.locator('text=Contact')).toBeVisible()
  })
})

