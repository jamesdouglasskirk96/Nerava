/**
 * Centralized CTA link helpers
 * All CTAs use environment variables for production, with fallbacks for development
 */

const DRIVER_FORM_FALLBACK = 'https://forms.gle/J6Rv2yo6uiQvH4pj7'
const MERCHANT_FORM_FALLBACK = 'https://forms.gle/5gvVWqXrhSWwReDJA'
const CHARGER_OWNER_FORM_FALLBACK = 'https://forms.gle/2HY3p3882yhqMkT69'

// Default to localhost apps in development (these need to be running)
// To start them:
// - Driver app: cd apps/driver && npm run dev (runs on port 5173)
// - Merchant app: cd apps/merchant && npm run dev (runs on port 5174)
const DEFAULT_DRIVER_APP_URL = 'http://localhost:5173'
const DEFAULT_MERCHANT_APP_URL = 'http://localhost:5174'

/**
 * Get driver app CTA URL with tracking parameters
 * Uses NEXT_PUBLIC_DRIVER_APP_URL in production, falls back to app.nerava.network
 * If the app isn't running, the link will fail - user should start the driver app first
 */
export function getDriverCTAHref(): string {
  // Production URL fallback
  const PRODUCTION_DRIVER_APP_URL = 'https://app.nerava.network'
  
  // If NEXT_PUBLIC_DRIVER_APP_URL is set, use it (production build)
  if (process.env.NEXT_PUBLIC_DRIVER_APP_URL) {
    return `${process.env.NEXT_PUBLIC_DRIVER_APP_URL}?src=landing&cta=driver`
  }
  
  // Check if we're in production mode (static export)
  const isProduction = process.env.NODE_ENV === 'production' || typeof window === 'undefined'
  
  if (isProduction) {
    // In production, use production URL (HTTP for now)
    return `${PRODUCTION_DRIVER_APP_URL}?src=landing&cta=driver`
  }
  
  // Development: use localhost default
  return `${DEFAULT_DRIVER_APP_URL}?src=landing&cta=driver`
}

/**
 * Get merchant app CTA URL with tracking parameters
 * Uses NEXT_PUBLIC_MERCHANT_APP_URL in production, falls back to merchant.nerava.network
 * If the app isn't running, the link will fail - user should start the merchant app first
 */
export function getMerchantCTAHref(): string {
  // Production URL fallback
  const PRODUCTION_MERCHANT_APP_URL = 'https://merchant.nerava.network'
  
  // If NEXT_PUBLIC_MERCHANT_APP_URL is set, use it (production build)
  if (process.env.NEXT_PUBLIC_MERCHANT_APP_URL) {
    return `${process.env.NEXT_PUBLIC_MERCHANT_APP_URL}?src=landing&cta=merchant`
  }
  
  // Check if we're in production mode (static export)
  const isProduction = process.env.NODE_ENV === 'production' || typeof window === 'undefined'
  
  if (isProduction) {
    // In production, use production URL (HTTP for now)
    return `${PRODUCTION_MERCHANT_APP_URL}?src=landing&cta=merchant`
  }
  
  // Development: use localhost default
  return `${DEFAULT_MERCHANT_APP_URL}?src=landing&cta=merchant`
}

/**
 * Get charger owner CTA URL
 * Uses NEXT_PUBLIC_CHARGER_PORTAL_URL if set, otherwise falls back to form
 */
export function getChargerOwnerCTAHref(): string {
  const chargerPortalUrl = process.env.NEXT_PUBLIC_CHARGER_PORTAL_URL
  
  if (chargerPortalUrl) {
    return `${chargerPortalUrl}?src=landing&cta=charger-owner`
  }
  
  return CHARGER_OWNER_FORM_FALLBACK
}

/**
 * Get merchant find/funnel CTA URL with tracking parameters
 * Routes to the /find page in the merchant app
 */
export function getMerchantFindHref(): string {
  const PRODUCTION_MERCHANT_APP_URL = 'https://merchant.nerava.network'

  if (process.env.NEXT_PUBLIC_MERCHANT_APP_URL) {
    return `${process.env.NEXT_PUBLIC_MERCHANT_APP_URL}/find?src=landing&cta=merchant`
  }

  const isProduction = process.env.NODE_ENV === 'production' || typeof window === 'undefined'

  if (isProduction) {
    return `${PRODUCTION_MERCHANT_APP_URL}/find?src=landing&cta=merchant`
  }

  return `${DEFAULT_MERCHANT_APP_URL}/find?src=landing&cta=merchant`
}

// Legacy exports for backward compatibility (deprecated, use helper functions instead)
// Note: These are evaluated at build time, so they use build-time env vars
// For runtime env vars, always use the helper functions directly
export const DRIVER_CTA_HREF = DEFAULT_DRIVER_APP_URL
export const MERCHANT_CTA_HREF = DEFAULT_MERCHANT_APP_URL
export const CHARGER_OWNER_CTA_HREF = CHARGER_OWNER_FORM_FALLBACK



