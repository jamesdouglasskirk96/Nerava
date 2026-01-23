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
}

export interface NextActions {
  request_wallet_pass: boolean
  require_vehicle_onboarding: boolean
}

export interface CaptureIntentResponse {
  session_id: string
  confidence_tier: 'A' | 'B' | 'C'
  charger_summary?: ChargerSummary
  merchants: MerchantSummary[]
  fallback_message?: string
  next_actions: NextActions
}

export interface MerchantInfo {
  id: string
  name: string
  category: string
  photo_url?: string
  address?: string
  rating?: number
  price_level?: number
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

// Party Cluster Types
export interface MerchantCard {
  id: string
  name: string
  address?: string
  photo_url?: string
  photo_urls?: string[]
  description?: string
  distance_to_charger?: number
  activations_today: number
  verified_visits_today: number
  offer_preview?: {
    title: string
    description: string
    nova_reward: number
  }
  is_primary: boolean
}

export interface ClusterResponse {
  cluster_id: string
  charger_radius_m: number
  merchant_radius_m: number
  primary_merchant: MerchantCard
  merchants: MerchantCard[]
}

// Exclusive Activation Types
export interface ActivateExclusiveRequest {
  merchant_id?: string
  merchant_place_id?: string
  charger_id: string
  charger_place_id?: string
  intent_session_id?: string
  lat: number
  lng: number
  accuracy_m?: number
}

export interface ExclusiveSessionResponse {
  id: string
  merchant_id?: string
  charger_id?: string
  expires_at: string
  activated_at: string
  remaining_seconds: number
}

export interface ActivateExclusiveResponse {
  status: string
  exclusive_session: ExclusiveSessionResponse
}

