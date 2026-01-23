import { test, expect } from '@playwright/test'

test.describe('Intent Capture Auth Required', () => {
  test('shows sign in required when auth is missing', async ({ page, context }) => {
    // Set geolocation
    await context.grantPermissions(['geolocation'])
    await context.setGeolocation({ latitude: 30.2672, longitude: -97.7431 })
    
    // Navigate to /wyc
    await page.goto('/wyc')
    
    // Assert "Sign in Required" state appears (not infinite loading)
    await expect(page.getByText(/Sign in Required/i)).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/Loading merchants/i)).not.toBeVisible()
    
    // Assert "Continue with Google" button is present
    await expect(page.getByRole('button', { name: /Continue with Google/i })).toBeVisible()
  })
})




