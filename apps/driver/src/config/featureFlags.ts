/**
 * Feature flags for gradual rollout.
 * Controlled via environment variables.
 */
export const FEATURE_FLAGS = {
  /**
   * V3 "Secure a Spot" flow with intent capture.
   * When false: uses legacy "Activate Exclusive" flow.
   * When true: uses new RefuelIntentModal → SpotSecuredModal flow.
   */
  SECURE_A_SPOT_V3: import.meta.env.VITE_SECURE_A_SPOT_V3 === 'true',
  /**
   * Live Coordination UI V1 - Transform from passive discovery to live coordination.
   * When false: uses existing passive headlines and UI.
   * When true: uses live intel headlines, social proof badges, stall indicators, and fullscreen ticket.
   */
  LIVE_COORDINATION_UI_V1: import.meta.env.VITE_LIVE_COORDINATION_UI_V1 === 'true',
} as const

export type FeatureFlags = typeof FEATURE_FLAGS
