/**
 * Analytics event name constants for driver app
 * 
 * DO NOT use string literals in components - always import from here
 */

export const DRIVER_EVENTS = {
  // Session
  SESSION_START: 'driver.session.start',
  
  // Page views
  PAGE_VIEW: 'driver.page.view',
  
  // OTP flow
  OTP_START: 'driver.otp.start',
  OTP_VERIFY_SUCCESS: 'driver.otp.verify.success',
  OTP_VERIFY_FAIL: 'driver.otp.verify.fail',
  // Button click events (snake_case format for consistency)
  OTP_SEND_CODE_CLICKED: 'driver_otp_send_code_clicked',
  OTP_VERIFY_CLICKED: 'driver_otp_verify_clicked',
  
  // Intent capture
  INTENT_CAPTURE_REQUEST: 'driver.intent.capture.request',
  INTENT_CAPTURE_SUCCESS: 'driver.intent.capture.success',
  INTENT_CAPTURE_FAIL: 'driver.intent.capture.fail',
  
  // Exclusive activation
  EXCLUSIVE_ACTIVATE_CLICK: 'driver.exclusive.activate.click',
  EXCLUSIVE_ACTIVATE_CLICKED: 'driver_activate_exclusive_clicked', // snake_case alias
  EXCLUSIVE_ACTIVATE_BLOCKED_OUTSIDE_RADIUS: 'driver.exclusive.activate.blocked_outside_radius',
  EXCLUSIVE_ACTIVATE_SUCCESS: 'driver.exclusive.activate.success',
  EXCLUSIVE_ACTIVATE_FAIL: 'driver.exclusive.activate.fail',
  
  // Exclusive completion
  EXCLUSIVE_COMPLETE_CLICK: 'driver.exclusive.complete.click',
  EXCLUSIVE_DONE_CLICKED: 'driver_exclusive_done_clicked', // snake_case alias
  EXCLUSIVE_COMPLETE_SUCCESS: 'driver.exclusive.complete.success',
  EXCLUSIVE_COMPLETE_FAIL: 'driver.exclusive.complete.fail',
  
  // Location
  LOCATION_PERMISSION_GRANTED: 'driver.location.permission.granted',
  LOCATION_PERMISSION_DENIED: 'driver.location.permission.denied',
  
  // CTAs
  CTA_OPEN_MAPS_CLICK: 'driver.cta.open_maps.click',
  GET_DIRECTIONS_CLICKED: 'driver_get_directions_clicked',
  IM_AT_MERCHANT_CLICKED: 'driver_im_at_merchant_clicked',
  
  // Arrival confirmation
  ARRIVAL_DONE_CLICKED: 'driver_arrival_done_clicked',
  
  // Preferences
  PREFERENCES_SUBMIT: 'driver.preferences.submit',
  PREFERENCES_DONE_CLICKED: 'driver_preferences_done_clicked', // snake_case alias
} as const

export type DriverEventName = typeof DRIVER_EVENTS[keyof typeof DRIVER_EVENTS]

