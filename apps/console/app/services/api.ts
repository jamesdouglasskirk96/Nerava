/**
 * Campaign Console API Client
 *
 * Provides typed API calls for campaign management, charger utilization,
 * and session data. Talks to /v1/campaigns/* and /v1/charging-sessions/* endpoints.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// --- Auth ---

function getToken(): string | null {
  return localStorage.getItem('access_token')
}

export function setToken(token: string) {
  localStorage.setItem('access_token', token)
}

export function clearToken() {
  localStorage.removeItem('access_token')
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

// --- Fetch wrapper ---

async function fetchAPI<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `API error: ${res.status}`)
  }

  return res.json()
}

// --- Types ---

export interface Campaign {
  id: string
  sponsor_name: string
  sponsor_email: string | null
  sponsor_logo_url: string | null
  sponsor_type: string | null
  name: string
  description: string | null
  campaign_type: string
  status: 'draft' | 'active' | 'paused' | 'exhausted' | 'completed' | 'canceled'
  priority: number
  budget_cents: number
  spent_cents: number
  cost_per_session_cents: number
  max_sessions: number | null
  sessions_granted: number
  start_date: string
  end_date: string | null
  auto_renew: boolean
  auto_renew_budget_cents: number | null
  max_grants_per_driver_per_day: number | null
  max_grants_per_driver_per_campaign: number | null
  max_grants_per_driver_per_charger: number | null
  rules: CampaignRules
  created_at: string
  updated_at: string
}

export interface CampaignRules {
  charger_ids: string[] | null
  charger_networks: string[] | null
  zone_ids: string[] | null
  geo_center_lat: number | null
  geo_center_lng: number | null
  geo_radius_m: number | null
  time_start: string | null
  time_end: string | null
  days_of_week: number[] | null
  min_duration_minutes: number
  max_duration_minutes: number | null
  min_power_kw: number | null
  connector_types: string[] | null
  driver_session_count_min: number | null
  driver_session_count_max: number | null
  driver_allowlist: string[] | null
}

export interface IncentiveGrant {
  id: string
  session_event_id: string
  campaign_id: string
  driver_user_id: number
  amount_cents: number
  status: 'pending' | 'granted' | 'clawed_back'
  granted_at: string | null
  created_at: string
  charger_id: string | null
  duration_minutes: number | null
}

export interface BudgetStatus {
  budget_cents: number
  spent_cents: number
  remaining_cents: number
  pct_used: number
  sessions_granted: number
  max_sessions: number | null
}

export interface ChargerUtilization {
  charger_id: string
  total_sessions: number
  unique_drivers: number
  avg_duration_minutes: number
}

export interface CreateCampaignInput {
  sponsor_name: string
  sponsor_email?: string
  sponsor_logo_url?: string
  sponsor_type?: string
  name: string
  description?: string
  campaign_type: string
  priority?: number
  budget_cents: number
  cost_per_session_cents: number
  max_sessions?: number
  start_date: string
  end_date?: string
  auto_renew?: boolean
  auto_renew_budget_cents?: number
  rules?: Partial<CampaignRules>
  caps?: {
    per_day?: number
    per_campaign?: number
    per_charger?: number
  }
}

// --- Campaign API ---

export async function listCampaigns(params?: {
  status?: string
  sponsor_name?: string
  limit?: number
  offset?: number
}): Promise<{ campaigns: Campaign[]; count: number }> {
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.sponsor_name) qs.set('sponsor_name', params.sponsor_name)
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const query = qs.toString() ? `?${qs}` : ''
  return fetchAPI(`/v1/campaigns/${query}`)
}

export async function getCampaign(id: string): Promise<{ campaign: Campaign }> {
  return fetchAPI(`/v1/campaigns/${id}`)
}

export async function createCampaign(
  input: CreateCampaignInput,
): Promise<{ campaign: Campaign }> {
  return fetchAPI('/v1/campaigns/', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function updateCampaign(
  id: string,
  input: Partial<CreateCampaignInput>,
): Promise<{ campaign: Campaign }> {
  return fetchAPI(`/v1/campaigns/${id}`, {
    method: 'PUT',
    body: JSON.stringify(input),
  })
}

export async function activateCampaign(
  id: string,
): Promise<{ campaign: Campaign }> {
  return fetchAPI(`/v1/campaigns/${id}/activate`, { method: 'POST' })
}

export async function pauseCampaign(
  id: string,
  reason?: string,
): Promise<{ campaign: Campaign }> {
  const qs = reason ? `?reason=${encodeURIComponent(reason)}` : ''
  return fetchAPI(`/v1/campaigns/${id}/pause${qs}`, { method: 'POST' })
}

export async function resumeCampaign(
  id: string,
): Promise<{ campaign: Campaign }> {
  return fetchAPI(`/v1/campaigns/${id}/resume`, { method: 'POST' })
}

export async function getCampaignGrants(
  campaignId: string,
  params?: { limit?: number; offset?: number },
): Promise<{ grants: IncentiveGrant[]; total: number; count: number }> {
  const qs = new URLSearchParams()
  if (params?.limit) qs.set('limit', String(params.limit))
  if (params?.offset) qs.set('offset', String(params.offset))
  const query = qs.toString() ? `?${qs}` : ''
  return fetchAPI(`/v1/campaigns/${campaignId}/grants${query}`)
}

export async function getCampaignBudget(
  campaignId: string,
): Promise<BudgetStatus> {
  return fetchAPI(`/v1/campaigns/${campaignId}/budget`)
}

// --- Utilization API ---

export async function getChargerUtilization(params?: {
  charger_ids?: string
  since_days?: number
}): Promise<{ chargers: ChargerUtilization[] }> {
  const qs = new URLSearchParams()
  if (params?.charger_ids) qs.set('charger_ids', params.charger_ids)
  if (params?.since_days) qs.set('since_days', String(params.since_days))
  const query = qs.toString() ? `?${qs}` : ''
  return fetchAPI(`/v1/campaigns/utilization/chargers${query}`)
}
