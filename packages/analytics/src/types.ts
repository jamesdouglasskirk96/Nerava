/**
 * Analytics configuration types
 */

export interface AnalyticsConfig {
  enabled?: boolean
  host?: string
  key?: string
  debug?: boolean
}

export interface AnalyticsClient {
  init: (appName: string, config?: AnalyticsConfig) => void
  track: (event: string, props?: Record<string, any>) => void
  identify: (distinctId: string, props?: Record<string, any>) => void
  setUserProps: (props: Record<string, any>) => void
  reset: () => void
}




