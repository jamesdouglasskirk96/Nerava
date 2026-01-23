/**
 * PostHog analytics wrapper for merchant app
 * 
 * This wrapper ensures:
 * - Single source of truth for PostHog initialization
 * - Consistent event properties across all events
 * - Error handling that never breaks user flows
 * - Anonymous ID persistence
 */

import posthog, { type PostHog } from 'posthog-js'
import { MERCHANT_EVENTS } from './events'

const ANON_ID_KEY = 'nerava_merchant_anon_id'
const ENV = import.meta.env.MODE === 'production' ? 'prod' : 'dev'

let isInitialized = false
let anonymousId: string | null = null

/**
 * Get or create anonymous ID from localStorage
 */
function getOrCreateAnonymousId(): string {
  if (anonymousId) {
    return anonymousId
  }
  
  let stored = localStorage.getItem(ANON_ID_KEY)
  if (!stored) {
    stored = `anon_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`
    localStorage.setItem(ANON_ID_KEY, stored)
  }
  anonymousId = stored
  return stored
}

/**
 * Initialize PostHog analytics
 * Call this once before rendering the app
 */
export function init(): void {
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
    posthog.init(posthogKey, {
      api_host: posthogHost,
      loaded: (ph: PostHog) => {
        const anonId = getOrCreateAnonymousId()
        ph.identify(anonId)
        
        ph.register({
          app: 'merchant',
          env: ENV,
        })
        
        if (import.meta.env.DEV) {
          console.log('[Analytics] PostHog initialized', { anonId })
        }
      },
      capture_pageview: false,
      capture_pageleave: false,
    })
    
    isInitialized = true
  } catch (error) {
    console.error('[Analytics] Failed to initialize PostHog:', error)
  }
}

/**
 * Identify a user (call after login)
 */
export function identify(userId: string, traits?: Record<string, unknown>): void {
  if (!isInitialized) {
    return
  }

  try {
    posthog.identify(userId, {
      ...traits,
      app: 'merchant',
      env: ENV,
    })
    
    posthog.setPersonProperties({
      merchant_user_id: userId,
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
 * Capture an event
 */
export function capture(
  eventName: string,
  properties?: Record<string, unknown>
): void {
  if (!isInitialized) {
    return
  }

  try {
    getOrCreateAnonymousId()
    
    const storedSource = localStorage.getItem('nerava_source')
    const storedCta = localStorage.getItem('nerava_cta')
    const storedUtm = localStorage.getItem('nerava_utm')
    
    const enrichedProperties = {
      app: 'merchant',
      env: ENV,
      source: 'ui',
      ts: new Date().toISOString(),
      ...(storedSource && { src: storedSource }),
      ...(storedCta && { cta: storedCta }),
      ...(storedUtm && { utm: JSON.parse(storedUtm) }),
      ...properties,
    }
    
    posthog.capture(eventName, enrichedProperties)
    
    if (import.meta.env.DEV) {
      console.log('[Analytics] Event captured', eventName, enrichedProperties)
    }
  } catch (error) {
    console.error('[Analytics] Failed to capture event:', error)
  }
}

/**
 * Reset analytics (call on logout)
 */
export function reset(): void {
  if (!isInitialized) {
    return
  }

  try {
    posthog.reset()
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
export { MERCHANT_EVENTS }




