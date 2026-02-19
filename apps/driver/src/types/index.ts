// Types matching backend schemas

export interface CaptureIntentRequest {
  lat: number
  lng: number
  accuracy_m?: number
  client_ts?: string
}

export interface ChargerSummary {
  id: string
  name: string
  distance_m: number
  network_name?: string
}

export interface MerchantSummary {
  place_id: string
  name: string
  lat: number
  lng: number
  distance_m: number
  types: string[]
  photo_url?: string
  icon_url?: string
  badges?: string[]
  daily_cap_cents?: number
  // Primary merchant override fields
  is_primary?: boolean
  exclusive_title?: string
  exclusive_description?: string
  open_now?: boolean
  open_until?: string
  rating?: number
  user_rating_count?: number
}

export interface NextActions {
  request_wallet_pass: boolean
  require_vehicle_onboarding: boolean
}

export interface CaptureIntentResponse {
  session_id: string
  confidence_tier: 'A' | 'B' | 'C'
  charger_summary?: ChargerSummary  // Nearest charger (backward compat)
  chargers?: ChargerSummary[]  // Up to 5 nearest chargers within 25km
  merchants: MerchantSummary[]
  fallback_message?: string
  next_actions: NextActions
}

export interface MerchantInfo {
  id: string
  place_id?: string
  name: string
  category: string
  description?: string
  photo_url?: string
  address?: string
  rating?: number
  price_level?: number
  amenities?: {
    bathroom: { upvotes: number; downvotes: number }
    wifi: { upvotes: number; downvotes: number }
  }
}

export interface MomentInfo {
  label: string
  distance_miles: number
  moment_copy: string
}

export interface PerkInfo {
  title: string
  badge: string
  description: string
}

export interface WalletInfo {
  can_add: boolean
  state: 'INACTIVE' | 'ACTIVE'
  active_copy?: string
}

export interface ActionsInfo {
  add_to_wallet: boolean
  get_directions_url?: string
}

export interface MerchantDetailsResponse {
  merchant: MerchantInfo
  moment: MomentInfo
  perk: PerkInfo
  wallet: WalletInfo
  actions: ActionsInfo
}

export interface WalletActivateRequest {
  session_id: string
  merchant_id: string
}

export interface WalletState {
  state: 'ACTIVE'
  merchant_id: string
  expires_at: string
  active_copy: string
}

export interface WalletActivateResponse {
  status: string
  wallet_state: WalletState
}

