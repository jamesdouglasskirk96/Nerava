/**
 * Centralized CTA link helpers
 * Production URLs for Nerava apps
 */

// S3 static website URLs (direct access for testing)
const DRIVER_APP_URL = 'http://app.nerava.network.s3-website-us-east-1.amazonaws.com'
const MERCHANT_APP_URL = 'http://merchant.nerava.network.s3-website-us-east-1.amazonaws.com'
const ADMIN_APP_URL = 'http://admin.nerava.network.s3-website-us-east-1.amazonaws.com'

// Fallback forms (for when apps are not yet available)
const DRIVER_FORM_FALLBACK = 'https://forms.gle/J6Rv2yo6uiQvH4pj7'
const MERCHANT_FORM_FALLBACK = 'https://forms.gle/5gvVWqXrhSWwReDJA'
const CHARGER_OWNER_FORM_FALLBACK = 'https://forms.gle/2HY3p3882yhqMkT69'

/**
 * Get driver app CTA URL with tracking parameters
 */
export function getDriverCTAHref(): string {
  return `${DRIVER_APP_URL}?src=landing&cta=driver`
}

/**
 * Get merchant app CTA URL with tracking parameters
 */
export function getMerchantCTAHref(): string {
  return `${MERCHANT_APP_URL}?src=landing&cta=merchant`
}

/**
 * Get charger owner/admin CTA URL with tracking parameters
 */
export function getChargerOwnerCTAHref(): string {
  return `${ADMIN_APP_URL}?src=landing&cta=charger-owner`
}

// Legacy exports for backward compatibility
export const DRIVER_CTA_HREF = DRIVER_APP_URL
export const MERCHANT_CTA_HREF = MERCHANT_APP_URL
export const CHARGER_OWNER_CTA_HREF = ADMIN_APP_URL



