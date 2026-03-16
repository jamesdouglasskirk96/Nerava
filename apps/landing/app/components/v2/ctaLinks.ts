/**
 * Centralized CTA link helpers
 * All CTAs use environment variables for production, with fallbacks for development
 */

const CHARGER_OWNER_FORM_FALLBACK = 'https://forms.gle/2HY3p3882yhqMkT69'

const DEFAULT_DRIVER_APP_URL = 'http://localhost:5173'
const DEFAULT_MERCHANT_APP_URL = 'http://localhost:5174'
const DEFAULT_CONSOLE_APP_URL = 'http://localhost:5176'

// App store links — update APP_STORE_URL once the App Store listing is live
export const APP_STORE_URL = 'https://apps.apple.com/us/app/nerava/id6759253986'
export const PLAY_STORE_URL = 'https://play.google.com/store/apps/details?id=network.nerava.app'
export const WEB_APP_URL = 'https://app.nerava.network'

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

/**
 * Get sponsor console CTA URL with tracking parameters
 */
export function getSponsorCTAHref(): string {
  const PRODUCTION_CONSOLE_URL = 'https://console.nerava.network'

  if (process.env.NEXT_PUBLIC_CONSOLE_APP_URL) {
    return `${process.env.NEXT_PUBLIC_CONSOLE_APP_URL}?src=landing&cta=sponsor`
  }

  const isProduction = process.env.NODE_ENV === 'production' || typeof window === 'undefined'

  if (isProduction) {
    return `${PRODUCTION_CONSOLE_URL}?src=landing&cta=sponsor`
  }

  return `${DEFAULT_CONSOLE_APP_URL}?src=landing&cta=sponsor`
}



