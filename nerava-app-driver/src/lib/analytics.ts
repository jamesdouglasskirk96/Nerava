import posthog from 'posthog-js'

let initialized = false

export function initAnalytics() {
  const apiKey = import.meta.env.VITE_POSTHOG_KEY
  const host = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com'

  if (!apiKey) {
    console.log('[Analytics] No PostHog key configured')
    return
  }

  posthog.init(apiKey, {
    api_host: host,
    capture_pageview: true,
    capture_pageleave: true,
    persistence: 'localStorage',
    // Privacy settings
    mask_all_text: true,
    mask_all_element_attributes: true,
  })

  initialized = true
  console.log('[Analytics] PostHog initialized')
}

export function track(event: string, properties?: Record<string, unknown>) {
  if (!initialized) return

  // Never send raw coordinates
  const safeProps = { ...properties }
  delete safeProps.lat
  delete safeProps.lng
  delete safeProps.latitude
  delete safeProps.longitude

  posthog.capture(event, safeProps)
}

export function identify(userId: string, traits?: Record<string, unknown>) {
  if (!initialized) return
  posthog.identify(userId, traits)
}

// Pre-defined events
export const AnalyticsEvents = {
  APP_OPENED: 'app_opened',
  LOCATION_PERMISSION_PROMPTED: 'location_permission_prompted',
  LOCATION_PERMISSION_GRANTED: 'location_permission_granted',
  LOCATION_PERMISSION_DENIED: 'location_permission_denied',
  CHARGER_VIEWED: 'charger_viewed',
  MERCHANT_CARD_VIEWED: 'merchant_card_viewed',
  MERCHANT_DETAILS_OPENED: 'merchant_details_opened',
  EXCLUSIVE_TAP: 'exclusive_tap',
  OTP_STARTED: 'otp_started',
  OTP_VERIFIED: 'otp_verified',
  EXCLUSIVE_ACTIVATED: 'exclusive_activated',
} as const


