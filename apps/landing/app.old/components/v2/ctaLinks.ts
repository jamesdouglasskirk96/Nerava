/**
 * Centralized CTA link constants
 * Routes to appropriate portals based on environment
 */

const DRIVER_APP_URL = process.env.NEXT_PUBLIC_DRIVER_APP_URL || 'http://localhost:5173'
const MERCHANT_APP_URL = process.env.NEXT_PUBLIC_MERCHANT_APP_URL || 'http://localhost:5174'
const CHARGER_PORTAL_URL = process.env.NEXT_PUBLIC_CHARGER_PORTAL_URL || 'https://forms.gle/2HY3p3882yhqMkT69'

/**
 * Get UTM params from current URL for propagation (client-side only)
 */
function getUTMQueryString(): string {
  if (typeof window === 'undefined') {
    return ''
  }
  
  const urlParams = new URLSearchParams(window.location.search)
  const utmParams: string[] = []
  
  const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
  utmKeys.forEach(key => {
    const value = urlParams.get(key)
    if (value) {
      utmParams.push(`${key}=${encodeURIComponent(value)}`)
    }
  })
  
  return utmParams.length > 0 ? `&${utmParams.join('&')}` : ''
}

/**
 * Build CTA href with source tracking and UTM params
 * Call this function in client components to get href with query params
 */
export function getDriverCTAHref(): string {
  const separator = DRIVER_APP_URL.includes('?') ? '&' : '?'
  const utmParams = getUTMQueryString()
  return `${DRIVER_APP_URL}${separator}src=landing&cta=open_driver${utmParams}`
}

export function getMerchantCTAHref(): string {
  const separator = MERCHANT_APP_URL.includes('?') ? '&' : '?'
  const utmParams = getUTMQueryString()
  return `${MERCHANT_APP_URL}${separator}src=landing&cta=for_businesses${utmParams}`
}

// For backward compatibility, export base URLs (components will call functions)
export const DRIVER_CTA_HREF = DRIVER_APP_URL
export const MERCHANT_CTA_HREF = MERCHANT_APP_URL
export const CHARGER_OWNER_CTA_HREF = CHARGER_PORTAL_URL // External link, no tracking needed



