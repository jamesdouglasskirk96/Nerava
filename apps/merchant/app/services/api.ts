// Merchant Portal API Client
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

export class ApiError extends Error {
  status: number
  code?: string

  constructor(
    status: number,
    code?: string,
    message?: string
  ) {
    super(message || `API error: ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

/**
 * Check if JWT token is expired
 */
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const exp = payload.exp
    if (!exp) return false // No expiration claim
    return Date.now() >= exp * 1000
  } catch {
    return false // Invalid token format
  }
}

/**
 * Clear session data and redirect to claim page
 */
function clearSessionAndRedirect() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('businessClaimed')
  localStorage.removeItem('merchant_id')
  localStorage.removeItem('merchant_account_id')
  localStorage.removeItem('place_id')
  window.location.href = `${import.meta.env.BASE_URL}claim`
}

export async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const token = localStorage.getItem('access_token')

  // Check token expiry before making request
  if (token && isTokenExpired(token)) {
    clearSessionAndRedirect()
    throw new ApiError(401, 'token_expired', 'Session expired')
  }

  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  // Handle 401 Unauthorized - clear session and redirect
  if (response.status === 401) {
    clearSessionAndRedirect()
    throw new ApiError(401, 'unauthorized', 'Authentication required')
  }

  if (!response.ok) {
    let errorData: { error?: string; message?: string; detail?: string } = {}
    try {
      errorData = await response.json()
    } catch {
      errorData = { message: response.statusText }
    }
    const errorMessage = errorData.message || errorData.detail || response.statusText
    const errorCode = errorData.error
    throw new ApiError(response.status, errorCode, errorMessage)
  }

  return await response.json()
}

// Types
export interface Exclusive {
  id: string
  merchant_id: string
  title: string
  description?: string
  daily_cap?: number
  session_cap?: number
  eligibility: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateExclusiveRequest {
  title: string
  description?: string
  daily_cap?: number
  session_cap?: number
  eligibility?: string
}

export interface UpdateExclusiveRequest {
  title?: string
  description?: string
  daily_cap?: number
  session_cap?: number
  eligibility?: string
  is_active?: boolean
}

export interface MerchantAnalytics {
  merchant_id: string
  activations: number
  completes: number
  unique_drivers: number
  completion_rate: number
}

export interface Visit {
  id: string
  timestamp: string
  exclusive_id: string | null
  exclusive_title: string
  driver_id_anonymized: string
  verification_status: 'VERIFIED' | 'ACTIVE' | 'PARTIAL' | 'REJECTED'
  duration_minutes: number | null
  charger_id: string | null
  location_name: string | null
}

// API Functions
export async function getMerchantExclusives(merchantId: string): Promise<Exclusive[]> {
  return fetchAPI<Exclusive[]>(`/v1/merchants/${merchantId}/exclusives`)
}

export async function createExclusive(
  merchantId: string,
  request: CreateExclusiveRequest
): Promise<Exclusive> {
  return fetchAPI<Exclusive>(`/v1/merchants/${merchantId}/exclusives`, {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function updateExclusive(
  merchantId: string,
  exclusiveId: string,
  request: UpdateExclusiveRequest
): Promise<Exclusive> {
  return fetchAPI<Exclusive>(`/v1/merchants/${merchantId}/exclusives/${exclusiveId}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  })
}

export async function toggleExclusive(
  merchantId: string,
  exclusiveId: string,
  enabled: boolean
): Promise<{ ok: boolean; is_active: boolean }> {
  return fetchAPI(`/v1/merchants/${merchantId}/exclusives/${exclusiveId}/enable?enabled=${enabled}`, {
    method: 'POST',
  })
}

export async function getMerchantAnalytics(merchantId: string): Promise<MerchantAnalytics> {
  return fetchAPI<MerchantAnalytics>(`/v1/merchants/${merchantId}/analytics`)
}

export async function updateBrandImage(merchantId: string, brandImageUrl: string): Promise<{ ok: boolean; brand_image_url: string }> {
  return fetchAPI(`/v1/merchants/${merchantId}/brand-image`, {
    method: 'PUT',
    body: JSON.stringify({ brand_image_url: brandImageUrl }),
  })
}

export async function getMerchantVisits(
  merchantId: string,
  period: 'week' | 'month' | 'all' = 'week',
  status?: 'VERIFIED' | 'PARTIAL' | 'REJECTED',
  limit = 100,
  offset = 0
): Promise<{ visits: Visit[]; total: number; verified_count: number; period: string; limit: number; offset: number }> {
  const params = new URLSearchParams({
    period,
    limit: limit.toString(),
    offset: offset.toString(),
  })
  if (status) params.append('status', status)
  return fetchAPI<{ visits: Visit[]; total: number; verified_count: number; period: string; limit: number; offset: number }>(
    `/v1/merchants/${merchantId}/visits?${params.toString()}`
  )
}

// --- Google OAuth ---

export async function startGoogleOAuth(): Promise<{ auth_url: string; state: string }> {
  // Use raw fetch — this is an unauthenticated endpoint and fetchAPI would
  // redirect to /claim if an old expired token is in localStorage
  const url = `${API_BASE_URL}/v1/merchant/auth/google/start`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) {
    throw new ApiError(response.status, undefined, 'Failed to start Google OAuth')
  }
  return response.json()
}

export async function handleGoogleCallback(code: string, state: string): Promise<{
  success: boolean
  access_token: string
  refresh_token: string
  merchant_account_id: string
  user_email: string
  user_name: string
}> {
  // Use raw fetch — this is an unauthenticated endpoint and fetchAPI would
  // redirect to /claim if an old expired token is in localStorage
  const url = `${API_BASE_URL}/v1/merchant/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) {
    let errorData: { detail?: string; message?: string } = {}
    try { errorData = await response.json() } catch {}
    throw new ApiError(response.status, undefined, errorData.detail || errorData.message || 'Failed to complete Google sign-in')
  }
  return response.json()
}

export async function listGBPLocations(): Promise<{ locations: Array<{ location_id: string; name: string; address: string; place_id: string }> }> {
  return fetchAPI('/v1/merchant/locations')
}

export async function claimLocation(placeId: string, name?: string, address?: string): Promise<{ claim_id: string; place_id: string; status: string; merchant_id?: string }> {
  return fetchAPI('/v1/merchant/claim', {
    method: 'POST',
    body: JSON.stringify({ place_id: placeId, name, address }),
  })
}

export async function searchPlaces(query: string): Promise<Array<{ place_id: string; name: string; address: string | null; lat: number; lng: number; types: string[] }>> {
  return fetchAPI(`/v1/merchants/places/search?q=${encodeURIComponent(query)}`)
}

// --- Merchant Profile ---

export async function fetchMyMerchant(): Promise<{ merchant: { id: string; name: string; nova_balance: number; zone_slug: string; status: string }; transactions: any[] }> {
  return fetchAPI('/v1/merchants/me')
}

// --- Subscriptions ---

export async function createSubscription(placeId: string, plan: string): Promise<{ checkout_url: string; session_id: string }> {
  return fetchAPI('/v1/merchant/billing/subscribe', {
    method: 'POST',
    body: JSON.stringify({ place_id: placeId, plan }),
  })
}

export async function getSubscription(): Promise<{ subscription: any }> {
  return fetchAPI('/v1/merchant/billing/subscription')
}

export async function cancelSubscription(): Promise<{ ok: boolean }> {
  return fetchAPI('/v1/merchant/billing/cancel', { method: 'POST' })
}

export async function getBillingPortalUrl(): Promise<{ url: string }> {
  return fetchAPI('/v1/merchant/billing/portal', { method: 'POST' })
}

export interface Invoice {
  id: string
  amount_due: number
  status: string
  created: number
  invoice_pdf: string | null
  hosted_invoice_url: string | null
}

export async function getInvoices(limit = 20): Promise<{ invoices: Invoice[] }> {
  return fetchAPI(`/v1/merchant/billing/invoices?limit=${limit}`)
}

// --- Ad Stats ---

export async function getAdStats(period: string = '30d'): Promise<any> {
  return fetchAPI(`/v1/ads/impressions/stats?period=${period}`)
}

// --- Profile ---

export async function updateProfile(data: Record<string, any>): Promise<{ ok: boolean }> {
  return fetchAPI('/v1/merchants/me/profile', {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

// --- Loyalty ---

export interface LoyaltyCard {
  id: string
  merchant_id: string
  place_id: string | null
  program_name: string
  visits_required: number
  reward_cents: number
  reward_description: string | null
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface LoyaltyCustomer {
  driver_id_anonymized: string
  card_name: string
  visit_count: number
  visits_required: number
  last_visit_at: string | null
  reward_unlocked: boolean
  reward_claimed: boolean
}

export interface LoyaltyStats {
  enrolled_drivers: number
  total_visits: number
  rewards_unlocked: number
  rewards_claimed: number
}

export async function getLoyaltyCards(merchantId: string): Promise<LoyaltyCard[]> {
  return fetchAPI<LoyaltyCard[]>(`/v1/loyalty/cards?merchant_id=${merchantId}`)
}

export async function createLoyaltyCard(
  merchantId: string,
  data: { program_name: string; visits_required: number; reward_cents: number; reward_description?: string; place_id?: string }
): Promise<LoyaltyCard> {
  return fetchAPI<LoyaltyCard>(`/v1/loyalty/cards?merchant_id=${merchantId}`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateLoyaltyCard(
  merchantId: string,
  cardId: string,
  data: Partial<{ program_name: string; visits_required: number; reward_cents: number; reward_description: string; is_active: boolean }>
): Promise<LoyaltyCard> {
  return fetchAPI<LoyaltyCard>(`/v1/loyalty/cards/${cardId}?merchant_id=${merchantId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function getLoyaltyCustomers(
  merchantId: string,
  limit = 50,
  offset = 0
): Promise<{ customers: LoyaltyCustomer[]; total: number }> {
  return fetchAPI(`/v1/loyalty/customers?merchant_id=${merchantId}&limit=${limit}&offset=${offset}`)
}

export async function getLoyaltyStats(merchantId: string): Promise<LoyaltyStats> {
  return fetchAPI<LoyaltyStats>(`/v1/loyalty/stats?merchant_id=${merchantId}`)
}

// --- Toast POS ---

export async function getToastStatus(): Promise<{
  connected: boolean;
  restaurant_name?: string;
  restaurant_guid?: string;
  aov_cents?: number;
  last_synced?: string;
}> {
  return fetchAPI('/v1/merchant/pos/status')
}

export async function startToastConnect(): Promise<{ auth_url: string; state: string }> {
  return fetchAPI('/v1/merchant/pos/toast/connect')
}

export async function handleToastCallback(code: string, state: string): Promise<{
  connected: boolean;
  restaurant_name: string;
  restaurant_guid: string;
}> {
  return fetchAPI('/v1/merchant/pos/toast/callback', {
    method: 'POST',
    body: JSON.stringify({ code, state }),
  })
}

export async function disconnectToast(): Promise<{ ok: boolean }> {
  return fetchAPI('/v1/merchant/pos/toast/disconnect', { method: 'POST' })
}

export async function getToastAOV(): Promise<{
  aov_cents: number;
  order_count: number;
  period_days: number;
}> {
  return fetchAPI('/v1/merchant/pos/toast/aov')
}

// Auth
export interface MerchantAuthRequest {
  id_token: string
  place_id?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function merchantGoogleAuth(request: MerchantAuthRequest): Promise<TokenResponse> {
  const response = await fetchAPI<TokenResponse>('/v1/auth/merchant/google', {
    method: 'POST',
    body: JSON.stringify(request),
  })

  // Store token
  localStorage.setItem('access_token', response.access_token)

  return response
}

/**
 * Logout: clear session and redirect to claim page
 */
export function logout() {
  clearSessionAndRedirect()
}
