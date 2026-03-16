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
  campaign_reward_cents?: number
  lat?: number
  lng?: number
  num_evse?: number
  power_kw?: number
  connector_types?: string[]
  pricing_per_kwh?: number | null
  active_drivers?: number
  has_merchant_perk?: boolean
  merchant_perk_title?: string
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
  phone?: string | null
  website?: string | null
  rating?: number
  price_level?: number
  hours_today?: string | null
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

export interface MerchantRewardState {
  has_active_reward: boolean
  reward_description?: string | null
  reward_amount_cents?: number | null
  active_claim_id?: string | null
  active_claim_status?: string | null  // claimed | receipt_uploaded | approved | rejected | expired
  active_claim_expires_at?: string | null
  join_request_count: number
  user_has_requested: boolean
}

export interface MerchantDetailsResponse {
  merchant: MerchantInfo
  moment: MomentInfo
  perk: PerkInfo
  wallet: WalletInfo
  actions: ActionsInfo
  reward_state?: MerchantRewardState | null
}

export interface RequestToJoinResponse {
  id: string
  place_id: string
  merchant_name: string
  status: string
  request_count: number
  created_at: string
}

export interface ClaimRewardResponse {
  id: string
  merchant_name: string
  reward_description?: string | null
  status: string
  claimed_at: string
  expires_at: string
  remaining_seconds: number
}

export interface ReceiptUploadResponse {
  id: string
  reward_claim_id: string
  status: string
  ocr_merchant_name?: string | null
  ocr_total_cents?: number | null
  ocr_confidence?: number | null
  approved_reward_cents?: number | null
  rejection_reason?: string | null
}

export interface ClaimDetailResponse {
  id: string
  merchant_name: string
  reward_description?: string | null
  status: string
  claimed_at: string
  expires_at: string
  remaining_seconds: number
  receipt?: ReceiptUploadResponse | null
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

