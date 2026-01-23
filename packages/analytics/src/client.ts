/**
 * PostHog analytics wrapper for Nerava apps
 * 
 * This wrapper ensures:
 * - Single source of truth for PostHog initialization
 * - Consistent event properties across all events
 * - Error handling that never breaks user flows
 * - Anonymous ID persistence
 * - Dev-only by default (requires explicit enable)
 */

import posthog, { type PostHog } from 'posthog-js'

const ANON_ID_KEY = 'nerava_anon_id'
let isInitialized = false
let anonymousId: string | null = null
let currentAppName: string = 'unknown'
let debugMode = false

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
 * Initialize PostHog analytics
 * Call this once before rendering the app
 */
export function initAnalytics(appName: string, config?: {
  enabled?: boolean
  host?: string
  key?: string
  debug?: boolean
}): void {
  if (isInitialized) {
    if (debugMode) {
      console.log('[Analytics] Already initialized, skipping')
    }
    return
  }

  currentAppName = appName

  // Check environment variables (support both VITE_ and NEXT_PUBLIC_ prefixes)
  const isVite = typeof import.meta !== 'undefined' && import.meta.env
  const env = isVite ? import.meta.env : (typeof window !== 'undefined' ? (window as any).process?.env : {})
  
  const analyticsEnabled = config?.enabled ?? 
    env.VITE_POSTHOG_ENABLED === 'true' || 
    env.NEXT_PUBLIC_POSTHOG_ENABLED === 'true' ||
    false

  const posthogKey = config?.key ?? 
    env.VITE_POSTHOG_KEY ?? 
    env.NEXT_PUBLIC_POSTHOG_KEY ?? 
    ''

  const posthogHost = config?.host ?? 
    env.VITE_POSTHOG_HOST ?? 
    env.NEXT_PUBLIC_POSTHOG_HOST ?? 
    'http://localhost:8080'

  debugMode = config?.debug ?? 
    env.VITE_ANALYTICS_DEBUG === 'true' || 
    env.NEXT_PUBLIC_ANALYTICS_DEBUG === 'true' ||
    false

  if (!analyticsEnabled || !posthogKey) {
    if (debugMode) {
      console.log('[Analytics] Analytics disabled or PostHog key missing', {
        enabled: analyticsEnabled,
        hasKey: !!posthogKey,
        host: posthogHost
      })
    }
    return
  }

  try {
    const envType = env.MODE === 'production' || env.NODE_ENV === 'production' ? 'prod' : 'dev'

    posthog.init(posthogKey, {
      api_host: posthogHost,
      loaded: (ph: PostHog) => {
        // Set anonymous ID if we have one
        const anonId = getOrCreateAnonymousId()
        ph.identify(anonId)
        
        // Set super properties
        ph.register({
          app: appName,
          env: envType,
        })
        
        if (debugMode) {
          console.log('[Analytics] PostHog initialized', { 
            appName, 
            anonId, 
            host: posthogHost,
            env: envType
          })
        }
      },
      capture_pageview: false, // We'll capture page views manually if needed
      capture_pageleave: false,
      autocapture: false, // Disable automatic capture for better control
    })
    
    isInitialized = true
  } catch (error) {
    console.error('[Analytics] Failed to initialize PostHog:', error)
    // Don't throw - analytics failures shouldn't break the app
  }
}

/**
 * Identify a user (call after authentication)
 */
export function identify(distinctId: string, props?: Record<string, unknown>): void {
  if (!isInitialized) {
    if (debugMode) {
      console.log('[Analytics] Not initialized, skipping identify')
    }
    return
  }

  try {
    const env = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : {}
    const envType = env.MODE === 'production' || env.NODE_ENV === 'production' ? 'prod' : 'dev'

    posthog.identify(distinctId, {
      ...props,
      app: currentAppName,
      env: envType,
    })
    
    // Update distinct_id in PostHog
    posthog.setPersonProperties({
      user_id: distinctId,
      ...props,
    })
    
    if (debugMode) {
      console.log('[Analytics] Identified user', distinctId, props)
    }
  } catch (error) {
    console.error('[Analytics] Failed to identify user:', error)
  }
}

/**
 * Capture an event
 */
export function track(
  eventName: string,
  properties?: Record<string, unknown>
): void {
  if (!isInitialized) {
    if (debugMode) {
      console.log('[Analytics] Not initialized, skipping track', eventName)
    }
    return
  }

  try {
    // Ensure we have an anonymous ID
    getOrCreateAnonymousId()
    
    const env = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : {}
    const envType = env.MODE === 'production' || env.NODE_ENV === 'production' ? 'prod' : 'dev'
    
    // Get stored source/utm from localStorage (set by session.start)
    const storedSource = localStorage.getItem('nerava_source')
    const storedCta = localStorage.getItem('nerava_cta')
    const storedUtm = localStorage.getItem('nerava_utm')
    
    const enrichedProperties = {
      app: currentAppName,
      env: envType,
      source: 'ui',
      ts: new Date().toISOString(),
      path: typeof window !== 'undefined' ? window.location.pathname : '',
      ...(storedSource && { src: storedSource }),
      ...(storedCta && { cta: storedCta }),
      ...(storedUtm && { utm: JSON.parse(storedUtm) }),
      ...properties,
    }
    
    posthog.capture(eventName, enrichedProperties)
    
    if (debugMode) {
      console.log('[Analytics] Event captured', eventName, enrichedProperties)
    }
  } catch (error) {
    console.error('[Analytics] Failed to capture event:', error)
  }
}

/**
 * Set user properties (person properties in PostHog)
 */
export function setUserProps(props: Record<string, unknown>): void {
  if (!isInitialized) {
    if (debugMode) {
      console.log('[Analytics] Not initialized, skipping setUserProps')
    }
    return
  }

  try {
    posthog.setPersonProperties(props)
    
    if (debugMode) {
      console.log('[Analytics] User properties set', props)
    }
  } catch (error) {
    console.error('[Analytics] Failed to set user properties:', error)
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
    
    if (debugMode) {
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




