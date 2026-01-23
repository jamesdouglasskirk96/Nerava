'use client'

/**
 * PostHog analytics wrapper for landing page (Next.js)
 * 
 * This wrapper ensures:
 * - Single source of truth for PostHog initialization
 * - Consistent event properties across all events
 * - Error handling that never breaks user flows
 * - UTM parameter capture and propagation
 */

import { useEffect } from 'react'
import posthog from 'posthog-js'
import { usePathname, useSearchParams } from 'next/navigation'
import { LANDING_EVENTS } from './events'

const ENV = process.env.NODE_ENV === 'production' ? 'prod' : 'dev'

let isInitialized = false

/**
 * Initialize PostHog analytics
 * Call this once in a client component (e.g., layout)
 */
export function initPostHog(): void {
  if (isInitialized || typeof window === 'undefined') {
    return
  }

  const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY
  const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com'
  const analyticsEnabled = process.env.NEXT_PUBLIC_ANALYTICS_ENABLED !== 'false'

  if (!analyticsEnabled || !posthogKey) {
    if (ENV === 'dev') {
      console.log('[Analytics] Analytics disabled or PostHog key missing')
    }
    return
  }

  try {
    posthog.init(posthogKey, {
      api_host: posthogHost,
      loaded: (ph) => {
        // Set super properties
        ph.register({
          app: 'landing',
          env: ENV,
        })
        
        if (ENV === 'dev') {
          console.log('[Analytics] PostHog initialized')
        }
      },
      capture_pageview: false, // We'll capture page views manually
      capture_pageleave: false,
    })
    
    isInitialized = true
  } catch (error) {
    console.error('[Analytics] Failed to initialize PostHog:', error)
  }
}

/**
 * Capture an event
 */
export function capture(
  eventName: string,
  properties?: Record<string, unknown>
): void {
  if (!isInitialized || typeof window === 'undefined') {
    return
  }

  try {
    // Extract UTM params from URL
    const urlParams = new URLSearchParams(window.location.search)
    const utm: Record<string, string> = {}
    const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
    utmKeys.forEach(key => {
      const value = urlParams.get(key)
      if (value) {
        utm[key] = value
      }
    })
    
    const enrichedProperties = {
      app: 'landing',
      env: ENV,
      source: 'ui',
      ts: new Date().toISOString(),
      path: window.location.pathname,
      referrer: document.referrer || undefined,
      ...(Object.keys(utm).length > 0 && { ...utm }),
      ...properties,
    }
    
    posthog.capture(eventName, enrichedProperties)
    
    if (ENV === 'dev') {
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
  path?: string,
  properties?: Record<string, unknown>
): void {
  capture(LANDING_EVENTS.PAGE_VIEW, {
    path: path || (typeof window !== 'undefined' ? window.location.pathname : ''),
    ...properties,
  })
}

/**
 * Capture a CTA click
 */
export function captureCTAClick(
  ctaId: string,
  ctaText?: string,
  href?: string
): void {
  capture(LANDING_EVENTS.CTA_CLICK, {
    cta_id: ctaId,
    cta_text: ctaText,
    href: href,
  })
}

/**
 * Get UTM params as query string for propagation to apps
 */
export function getUTMQueryString(): string {
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

// Export events for use in components
export { LANDING_EVENTS }

