/**
 * Analytics event name constants for landing page
 * 
 * DO NOT use string literals in components - always import from here
 */

export const LANDING_EVENTS = {
  // Page views
  PAGE_VIEW: 'landing.page.view',
  
  // CTA clicks
  CTA_CLICK: 'landing.cta.click',
  
  // CTA conversion (when destination app loads)
  CTA_CONVERT: 'landing.cta.convert',
} as const

export type LandingEventName = typeof LANDING_EVENTS[keyof typeof LANDING_EVENTS]

