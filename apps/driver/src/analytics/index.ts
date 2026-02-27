/**
 * PostHog analytics wrapper for driver app
 *
 * This wrapper ensures:
 * - Single source of truth for PostHog initialization
 * - Consistent event properties across all events
 * - Error handling that never breaks user flows
 * - Anonymous ID persistence
 * - Lazy-loaded PostHog SDK to reduce initial bundle size
 */

import type { PostHog } from 'posthog-js'
import { DRIVER_EVENTS } from './events'

const ANON_ID_KEY = 'nerava_anon_id'
const ENV = import.meta.env.MODE === 'production' ? 'prod' : 'dev'

let isInitialized = false
let anonymousId: string | null = null
let posthogInstance: PostHog | null = null

/**
 * Get or create anonymous ID from localStorage
 */
function getOrCreateAnonymousId(): string {
  if (anonymousId) {
    return anonymousId
  }

  let stored = localStorage.getItem(ANON_ID_KEY)
  if (!stored) {
    // Generate a simple anonymous ID (PostHog will generate its own, but we persist ours)
    stored = `anon_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`
    localStorage.setItem(ANON_ID_KEY, stored)
  }
  anonymousId = stored
  return stored
}

/**
 * Initialize PostHog analytics (lazy-loads the PostHog SDK)
 * Call this once before rendering the app
 */
export async function init(): Promise<void> {
  if (isInitialized) {
    return
  }

  const posthogKey = import.meta.env.VITE_POSTHOG_KEY
  const posthogHost = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com'
  const analyticsEnabled = import.meta.env.VITE_ANALYTICS_ENABLED !== 'false'

  if (!analyticsEnabled || !posthogKey) {
    if (import.meta.env.DEV) {
      console.log('[Analytics] Analytics disabled or PostHog key missing')
    }
    return
  }

  try {
    // Lazy-load PostHog SDK to reduce initial bundle size
    const posthog = await import('posthog-js').then(m => m.default)
    posthogInstance = posthog

    posthog.init(posthogKey, {
      api_host: posthogHost,
      loaded: (ph: PostHog) => {
        // Set anonymous ID if we have one
        const anonId = getOrCreateAnonymousId()
        ph.identify(anonId)

        // Set super properties
        ph.register({
          app: 'driver',
          env: ENV,
        })

        if (import.meta.env.DEV) {
          console.log('[Analytics] PostHog initialized', { anonId })
        }
      },
      capture_pageview: false, // We'll capture page views manually
      capture_pageleave: false,
    })

    isInitialized = true
  } catch (error) {
    console.error('[Analytics] Failed to initialize PostHog:', error)
    // Don't throw - analytics failures shouldn't break the app
  }
}

/**
 * Check if analytics consent is granted
 */
async function hasAnalyticsConsent(): Promise<boolean> {
  // Check localStorage first
  const stored = localStorage.getItem('consent_analytics')
  if (stored === 'granted') {
    return true
  }
  if (stored === 'denied') {
    return false
  }

  // If not in localStorage, check API
  try {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'
    const token = localStorage.getItem('access_token')

    if (!token) {
      return false
    }

    const response = await fetch(`${API_BASE_URL}/v1/consent`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (response.ok) {
      const data = await response.json()
      const analyticsConsent = data.consents?.find((c: { consent_type: string }) => c.consent_type === 'analytics')
      const granted = analyticsConsent?.granted === true

      // Cache result in localStorage
      localStorage.setItem('consent_analytics', granted ? 'granted' : 'denied')
      return granted
    }
  } catch (error) {
    console.error('[Analytics] Failed to check consent:', error)
  }

  return false
}

/**
 * Identify a user (call after OTP verification)
 */
export function identify(userId: string, traits?: Record<string, unknown>): void {
  if (!isInitialized || !posthogInstance) {
    return
  }

  try {
    posthogInstance.identify(userId, {
      ...traits,
      app: 'driver',
      env: ENV,
    })

    // Update distinct_id in PostHog
    posthogInstance.setPersonProperties({
      driver_id: userId,
      ...traits,
    })

    if (import.meta.env.DEV) {
      console.log('[Analytics] Identified user', userId, traits)
    }
  } catch (error) {
    console.error('[Analytics] Failed to identify user:', error)
  }
}

/**
 * Identify a user only if analytics consent is granted
 */
export async function identifyIfConsented(userId: string, traits?: Record<string, unknown>): Promise<void> {
  const consented = await hasAnalyticsConsent()
  if (consented) {
    identify(userId, traits)
  } else {
    if (import.meta.env.DEV) {
      console.log('[Analytics] Skipping identify - analytics consent not granted')
    }
  }
}

/**
 * Get current location from browser (if available and permitted)
 * Returns null if location is unavailable or user denied permission
 */
async function getCurrentLocation(): Promise<{ lat: number; lng: number; accuracy_m?: number } | null> {
  if (!navigator.geolocation) {
    return null
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy_m: position.coords.accuracy || undefined,
        })
      },
      () => {
        // User denied or error - silently fail
        resolve(null)
      },
      {
        enableHighAccuracy: false,
        timeout: 2000,
        maximumAge: 60000, // Use cached location if < 1 minute old
      }
    )
  })
}

/**
 * Capture an event (synchronous wrapper for async implementation)
 *
 * @param eventName - Event name
 * @param properties - Event properties (can include lat/lng to override auto-detection)
 * @param includeGeo - Whether to automatically include geo coordinates (default: true)
 */
export function capture(
  eventName: string,
  properties?: Record<string, unknown>,
  includeGeo: boolean = true
): void {
  // Fire and forget - don't block the UI
  captureAsync(eventName, properties, includeGeo).catch((error) => {
    console.error('[Analytics] Failed to capture event:', error)
  })
}

/**
 * Capture an event (async version with geo coordinates)
 *
 * @param eventName - Event name
 * @param properties - Event properties (can include lat/lng to override auto-detection)
 * @param includeGeo - Whether to automatically include geo coordinates (default: true)
 */
async function captureAsync(
  eventName: string,
  properties?: Record<string, unknown>,
  includeGeo: boolean = true
): Promise<void> {
  if (!isInitialized || !posthogInstance) {
    return
  }

  try {
    // Ensure we have an anonymous ID
    getOrCreateAnonymousId()

    // Get stored source/utm from localStorage (set by session.start)
    const storedSource = localStorage.getItem('nerava_source')
    const storedCta = localStorage.getItem('nerava_cta')
    const storedUtm = localStorage.getItem('nerava_utm')

    // Get geo coordinates if requested and not already provided
    let geoData: { lat?: number; lng?: number; accuracy_m?: number } = {}
    if (includeGeo && !properties?.lat && !properties?.lng) {
      const location = await getCurrentLocation()
      if (location) {
        geoData = {
          lat: location.lat,
          lng: location.lng,
          ...(location.accuracy_m && { accuracy_m: location.accuracy_m }),
        }
      }
    } else if (properties?.lat && properties?.lng) {
      // Use provided coordinates
      geoData = {
        lat: properties.lat as number,
        lng: properties.lng as number,
      }
      if (properties.accuracy_m) {
        geoData.accuracy_m = properties.accuracy_m as number
      }
    }

    const enrichedProperties = {
      app: 'driver',
      env: ENV,
      source: 'ui',
      ts: new Date().toISOString(),
      ...(storedSource && { src: storedSource }),
      ...(storedCta && { cta: storedCta }),
      ...(storedUtm && { utm: JSON.parse(storedUtm) }),
      ...geoData, // Include geo coordinates
      ...properties, // Custom properties override geo if provided
    }

    posthogInstance.capture(eventName, enrichedProperties)

    if (import.meta.env.DEV) {
      console.log('[Analytics] Event captured', eventName, enrichedProperties)
    }
  } catch (error) {
    console.error('[Analytics] Failed to capture event:', error)
  }
}

/**
 * Capture a page view
 */
export function page(
  pageName: string,
  properties?: Record<string, unknown>
): void {
  capture(DRIVER_EVENTS.PAGE_VIEW, {
    page: pageName,
    ...properties,
  })
}

/**
 * Reset analytics (call on logout)
 */
export function reset(): void {
  if (!isInitialized || !posthogInstance) {
    return
  }

  try {
    posthogInstance.reset()
    anonymousId = null
    localStorage.removeItem(ANON_ID_KEY)
    localStorage.removeItem('nerava_source')
    localStorage.removeItem('nerava_cta')
    localStorage.removeItem('nerava_utm')

    if (import.meta.env.DEV) {
      console.log('[Analytics] Analytics reset')
    }
  } catch (error) {
    console.error('[Analytics] Failed to reset analytics:', error)
  }
}

/**
 * Store source/utm params from query string (called on app load)
 */
export function storeSourceParams(searchParams: URLSearchParams): void {
  const src = searchParams.get('src')
  const cta = searchParams.get('cta')

  // Extract UTM params
  const utm: Record<string, string> = {}
  const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
  utmKeys.forEach(key => {
    const value = searchParams.get(key)
    if (value) {
      utm[key] = value
    }
  })

  if (src) {
    localStorage.setItem('nerava_source', src)
  }
  if (cta) {
    localStorage.setItem('nerava_cta', cta)
  }
  if (Object.keys(utm).length > 0) {
    localStorage.setItem('nerava_utm', JSON.stringify(utm))
  }
}

// Export events for use in components
export { DRIVER_EVENTS }
