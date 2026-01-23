// Admin Portal API Client
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

export class ApiError extends Error {
  constructor(
    public status: number,
    public code?: string,
    message?: string
  ) {
    super(message || `API error: ${status}`)
    this.name = 'ApiError'
  }
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const token = localStorage.getItem('access_token')
  
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  })

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
export interface Merchant {
  id: string
  name: string
  status: string
  zone_slug: string
  nova_balance: number
  created_at: string
}

export interface Exclusive {
  id: string
  merchant_id: string
  merchant_name: string
  title: string
  description?: string
  nova_reward: number
  daily_cap?: number
  activations_today: number
  activations_this_month: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: string
  operator_id: number
  operator_email?: string
  action_type: string
  target_type: string
  target_id: string
  reason?: string
  ip_address?: string
  created_at: string
}

export interface ActiveSession {
  id: string
  driver_id: number
  merchant_id: string | null
  merchant_name: string | null
  charger_id: string | null
  charger_name: string | null
  status: string
  activated_at: string
  expires_at: string
  time_remaining_minutes: number
}

// API Functions
export async function searchMerchants(query: string): Promise<{ merchants: Merchant[] }> {
  return fetchAPI(`/v1/admin/merchants?query=${encodeURIComponent(query)}`)
}

export async function getMerchantStatus(merchantId: string): Promise<any> {
  return fetchAPI(`/v1/admin/merchants/${merchantId}/status`)
}

export async function getAllExclusives(status?: string, merchantId?: string): Promise<{ exclusives: Exclusive[]; total: number; limit: number; offset: number }> {
  const params = new URLSearchParams()
  if (status) params.append('status', status)
  if (merchantId) params.append('merchant_id', merchantId)
  const query = params.toString()
  const url = `/v1/admin/exclusives${query ? `?${query}` : ''}`
  return fetchAPI(url)
}

export async function toggleExclusive(exclusiveId: string, reason: string): Promise<{ exclusive_id: string; previous_state: boolean; new_state: boolean; toggled_by: string; reason: string }> {
  return fetchAPI(`/v1/admin/exclusives/${exclusiveId}/toggle`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function pauseMerchant(merchantId: string, reason: string): Promise<{ merchant_id: string; action: string; previous_status: string; new_status: string; reason: string }> {
  return fetchAPI(`/v1/admin/merchants/${merchantId}/pause`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function resumeMerchant(merchantId: string, reason: string): Promise<{ merchant_id: string; action: string; previous_status: string; new_status: string; reason: string }> {
  return fetchAPI(`/v1/admin/merchants/${merchantId}/resume`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function forceCloseSessions(locationId: string, reason: string): Promise<{ location_id: string; sessions_closed: number; closed_by: string; reason: string; timestamp: string }> {
  return fetchAPI('/v1/admin/sessions/force-close', {
    method: 'POST',
    body: JSON.stringify({ location_id: locationId, reason }),
  })
}

export async function emergencyPause(action: 'activate' | 'deactivate', reason: string, confirmation: string): Promise<{ action: string; activated_by: string; reason: string; timestamp: string }> {
  return fetchAPI('/v1/admin/overrides/emergency-pause', {
    method: 'POST',
    body: JSON.stringify({ action, reason, confirmation }),
  })
}

export async function setDemoLocation(lat: number, lng: number, chargerId?: string): Promise<any> {
  return fetchAPI('/v1/admin/demo/location', {
    method: 'POST',
    body: JSON.stringify({ lat, lng, charger_id: chargerId }),
  })
}

export async function getAuditLogs(limit = 100, offset = 0, type?: string, search?: string, startDate?: string, endDate?: string): Promise<{
  logs: AuditLog[]
  total: number
  limit: number
  offset: number
}> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  })
  if (type) params.append('type', type)
  if (search) params.append('search', search)
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)
  
  return fetchAPI(`/v1/admin/logs?${params.toString()}`)
}

export async function getActiveSessions(): Promise<{ sessions: ActiveSession[]; total_active: number }> {
  return fetchAPI('/v1/admin/sessions/active')
}

export async function sendMerchantPortalLink(merchantId: string, email: string): Promise<{ success: boolean }> {
  return fetchAPI(`/v1/admin/merchants/${merchantId}/send-portal-link`, {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export async function pauseMerchant(merchantId: string, reason: string): Promise<{ merchant_id: string; action: string; previous_status: string; new_status: string; reason: string }> {
  return fetchAPI(`/v1/admin/merchants/${merchantId}/pause`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function resumeMerchant(merchantId: string, reason: string): Promise<{ merchant_id: string; action: string; previous_status: string; new_status: string; reason: string }> {
  return fetchAPI(`/v1/admin/merchants/${merchantId}/resume`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

// Auth
export interface AdminLoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function adminLogin(request: AdminLoginRequest): Promise<TokenResponse> {
  const response = await fetchAPI<TokenResponse>('/v1/auth/admin/login', {
    method: 'POST',
    body: JSON.stringify(request),
  })
  
  localStorage.setItem('access_token', response.access_token)
  
  return response
}



