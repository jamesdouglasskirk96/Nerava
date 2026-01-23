// Mock-specific types that extend existing types
import type {
  CaptureIntentRequest,
  CaptureIntentResponse,
  MerchantSummary,
  ChargerSummary,
  MerchantDetailsResponse,
  WalletActivateResponse,
} from '../types'

export type ChargingState = 'charging' | 'pre-charging'

export interface MockCaptureIntentRequest extends CaptureIntentRequest {
  state?: ChargingState
}

export interface ChargerWithExperiences extends ChargerSummary {
  stalls: number
  plug_types: string[]
  rating: number
  nearby_experiences: MerchantSummary[]
}

export interface MockChargerDetailsResponse {
  charger: ChargerWithExperiences
}

// Re-export existing types for convenience
export type {
  CaptureIntentRequest,
  CaptureIntentResponse,
  MerchantSummary,
  ChargerSummary,
  MerchantDetailsResponse,
  WalletActivateResponse,
}

