/**
 * Analytics event name constants for merchant app
 * 
 * DO NOT use string literals in components - always import from here
 */

export const MERCHANT_EVENTS = {
  // Session
  SESSION_START: 'merchant.session.start',
  
  // Login
  LOGIN_SUCCESS: 'merchant.login.success',
  LOGIN_FAIL: 'merchant.login.fail',
  
  // Exclusive creation
  EXCLUSIVE_CREATE_OPEN: 'merchant.exclusive.create.open',
  EXCLUSIVE_CREATE_SUBMIT_SUCCESS: 'merchant.exclusive.create.submit.success',
  EXCLUSIVE_CREATE_SUBMIT_FAIL: 'merchant.exclusive.create.submit.fail',
  
  // Exclusive toggle
  EXCLUSIVE_TOGGLE_ON: 'merchant.exclusive.toggle.on',
  EXCLUSIVE_TOGGLE_OFF: 'merchant.exclusive.toggle.off',
  
  // Brand image upload
  BRAND_IMAGE_UPLOAD_SUCCESS: 'merchant.brand_image.upload.success',
  BRAND_IMAGE_UPLOAD_FAIL: 'merchant.brand_image.upload.fail',
  
  // Analytics view
  ANALYTICS_VIEW: 'merchant.analytics.view',

  // Merchant acquisition funnel
  FUNNEL_SEARCH: 'merchant.funnel.search',
  FUNNEL_SEARCH_NO_RESULTS: 'merchant.funnel.search.no_results',
  FUNNEL_SELECT_BUSINESS: 'merchant.funnel.select_business',
  FUNNEL_PREVIEW_LOADED: 'merchant.funnel.preview.loaded',
  FUNNEL_PREVIEW_ERROR: 'merchant.funnel.preview.error',
  FUNNEL_LOOM_OPENED: 'merchant.funnel.loom.opened',
  FUNNEL_LOOM_CLOSED: 'merchant.funnel.loom.closed',
  FUNNEL_LOOM_COMPLETED: 'merchant.funnel.loom.completed',
  FUNNEL_CTA_CLAIM: 'merchant.funnel.cta.claim',
  FUNNEL_CTA_SCHEDULE: 'merchant.funnel.cta.schedule',
  FUNNEL_CTA_TEXT_LINK: 'merchant.funnel.cta.text_link',
} as const

export type MerchantEventName = typeof MERCHANT_EVENTS[keyof typeof MERCHANT_EVENTS]







