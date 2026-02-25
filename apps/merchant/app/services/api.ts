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
  localStorage.removeItem('businessClaimed')
  localStorage.removeItem('merchant_id')
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
  verification_status: 'VERIFIED' | 'PARTIAL' | 'REJECTED'
  duration_minutes: number | null
  charger_id: string | null
  location_name: string | null
}

// API Functions
export async function getMerchantExclusives(merchantId: string): Promise<Exclusive[]> {
  // For MVP, we'll need to query MerchantPerk with is_exclusive flag
  // This is a simplified version - backend needs to add GET /v1/merchants/{id}/exclusives
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
