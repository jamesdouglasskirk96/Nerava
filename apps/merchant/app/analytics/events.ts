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
} as const

export type MerchantEventName = typeof MERCHANT_EVENTS[keyof typeof MERCHANT_EVENTS]




