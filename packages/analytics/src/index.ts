/**
 * Shared analytics package for Nerava apps
 * 
 * Provides a consistent PostHog wrapper across all applications
 */

export {
  initAnalytics,
  identify,
  track,
  setUserProps,
  reset,
  storeSourceParams,
} from './client'

export type { AnalyticsConfig, AnalyticsClient } from './types'







