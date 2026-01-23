/**
 * Analytics event name constants for admin app
 * 
 * DO NOT use string literals in components - always import from here
 */

export const ADMIN_EVENTS = {
  // Session
  SESSION_START: 'admin.session.start',
  
  // Login
  LOGIN_SUCCESS: 'admin.login.success',
  LOGIN_FAIL: 'admin.login.fail',
  
  // Demo location override
  DEMO_LOCATION_OVERRIDE_SET_SUCCESS: 'admin.demo_location.override.set.success',
  DEMO_LOCATION_OVERRIDE_SET_FAIL: 'admin.demo_location.override.set.fail',
  
  // Exclusive toggle
  EXCLUSIVE_TOGGLE_ON: 'admin.exclusive.toggle.on',
  EXCLUSIVE_TOGGLE_OFF: 'admin.exclusive.toggle.off',
  
  // Audit log
  AUDIT_LOG_VIEW: 'admin.audit_log.view',
  
  // Merchants view
  MERCHANTS_VIEW: 'admin.merchants.view',
  
  // Generic operation error
  OPERATION_ERROR: 'admin.operation.error',
} as const

export type AdminEventName = typeof ADMIN_EVENTS[keyof typeof ADMIN_EVENTS]




