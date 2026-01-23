import { useQuery, useMutation } from '@tanstack/react-query'
import type {
  CaptureIntentRequest,
  CaptureIntentResponse,
  MerchantDetailsResponse,
  WalletActivateRequest,
  WalletActivateResponse,
} from '../types'
import {
  captureIntentMock,
  getMerchantDetailsMock,
  activateExclusiveMock,
} from '../mock/mockApi'
import type { MockCaptureIntentRequest } from '../mock/types'
import {
  validateResponse,
  CaptureIntentResponseSchema,
  ActivateExclusiveResponseSchema,
  ActiveExclusiveResponseSchema,
  LocationCheckResponseSchema,
  MerchantDetailsResponseSchema,
} from './schemas'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

// Check if mock mode is enabled - default to backend mode unless explicitly set
export function isMockMode(): boolean {
  return import.meta.env.VITE_MOCK_MODE === 'true'
}

// Check if demo mode is enabled - allows mock data fallback when API fails
export function isDemoMode(): boolean {
  return import.meta.env.VITE_DEMO_MODE === 'true'
}

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

async function fetchAPI<T>(endpoint: string, options?: RequestInit, retryOn401 = true): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const token = localStorage.getItem('access_token')
  
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  console.log('[API] Fetching:', url, options)
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    console.log('[API] Response status:', response.status, response.statusText)

    // Handle 401 Unauthorized - try token refresh
    if (response.status === 401 && retryOn401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          console.log('[API] Attempting token refresh...')
          const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })

          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json()
            localStorage.setItem('access_token', refreshData.access_token)
            if (refreshData.refresh_token) {
              localStorage.setItem('refresh_token', refreshData.refresh_token)
            }
            console.log('[API] Token refreshed, retrying original request')
            
            // Retry original request with new token
            const newHeaders = new Headers(options?.headers)
            newHeaders.set('Content-Type', 'application/json')
            newHeaders.set('Authorization', `Bearer ${refreshData.access_token}`)
            const retryResponse = await fetch(url, {
              ...options,
              headers: newHeaders,
            })

            if (!retryResponse.ok) {
              // If retry still fails, clear tokens
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              throw new ApiError(retryResponse.status, undefined, 'Authentication failed after token refresh')
            }

            const retryData = await retryResponse.json()
            console.log('[API] Retry response data:', retryData)
            return retryData
          } else {
            // Refresh failed, clear tokens
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            throw new ApiError(401, 'refresh_failed', 'Token refresh failed')
          }
        } catch (refreshError) {
          // Refresh failed, clear tokens
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (refreshError instanceof ApiError) {
            throw refreshError
          }
          throw new ApiError(401, 'refresh_error', 'Failed to refresh token')
        }
      } else {
        // No refresh token, clear access token and throw
        localStorage.removeItem('access_token')
        throw new ApiError(401, 'no_refresh_token', 'No refresh token available')
      }
    }

    if (!response.ok) {
      let errorData: { error?: string; message?: string; detail?: string } = {}
      try {
        errorData = await response.json()
      } catch {
        // Not JSON, try to get text
        try {
          const errorText = await response.text()
          errorData = { message: errorText || response.statusText }
        } catch {
          errorData = { message: response.statusText }
        }
      }
      console.error('[API] Error response:', errorData)
      // Handle FastAPI's standard error format: {detail: "..."} or {error: "...", message: "..."}
      const errorMessage = errorData.message || errorData.detail || response.statusText
      const errorCode = errorData.error || (response.status >= 500 ? 'server_error' : undefined)
      throw new ApiError(
        response.status,
        errorCode,
        errorMessage
      )
    }

    const data = await response.json()
    console.log('[API] Response data:', data)
    return data
  } catch (error) {
    console.error('[API] Fetch error:', error)
    // Re-throw ApiError as-is, wrap other errors
    if (error instanceof ApiError) {
      console.error('[API] Throwing ApiError:', error.status, error.code, error.message)
      throw error
    }
    // Network errors or other fetch failures
    const apiError = new ApiError(0, 'network_error', error instanceof Error ? error.message : 'Network error')
    console.error('[API] Throwing wrapped ApiError:', apiError.status, apiError.code, apiError.message)
    throw apiError
  }
}

// Intent Capture
export function useIntentCapture(request: CaptureIntentRequest | null) {
  return useQuery({
    queryKey: ['intent-capture', request],
    queryFn: async () => {
      if (isMockMode() && request) {
        // Use mock API in mock mode
        return await captureIntentMock(request as MockCaptureIntentRequest)
      }
      // Use real API
      const data = await fetchAPI<unknown>('/v1/intent/capture', {
        method: 'POST',
        body: JSON.stringify(request),
      })
      // Validate response schema
      return validateResponse(CaptureIntentResponseSchema, data, '/v1/intent/capture') as unknown as CaptureIntentResponse
    },
    enabled: request !== null,
    retry: false, // Don't retry on error
    retryOnMount: false, // Don't retry on mount
    refetchOnWindowFocus: false, // Don't refetch on window focus
  })
}

// Merchant Details
export function useMerchantDetails(
  merchantId: string | null,
  sessionId?: string
) {
  return useQuery({
    queryKey: ['merchant-details', merchantId, sessionId],
    queryFn: async () => {
      if (isMockMode() && merchantId) {
        // Use mock API in mock mode
        return await getMerchantDetailsMock(merchantId, sessionId)
      }
      // Use real API
      const params = sessionId ? `?session_id=${sessionId}` : ''
      const data = await fetchAPI<unknown>(`/v1/merchants/${merchantId}${params}`)
      return validateResponse(MerchantDetailsResponseSchema, data, `/v1/merchants/${merchantId}`) as unknown as MerchantDetailsResponse
    },
    enabled: merchantId !== null,
  })
}

// Wallet Activate (legacy - use exclusive endpoints instead)
export function useWalletActivate() {
  return useMutation({
    mutationFn: async (request: WalletActivateRequest) => {
      if (isMockMode()) {
        // Use mock API in mock mode
        return await activateExclusiveMock(request.merchant_id, request.session_id)
      }
      // Use real API
      return fetchAPI<WalletActivateResponse>('/v1/wallet/pass/activate', {
        method: 'POST',
        body: JSON.stringify(request),
      })
    },
  })
}

// Exclusive Session Types
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

export interface CompleteExclusiveRequest {
  exclusive_session_id: string
  feedback?: {
    thumbs_up?: boolean
    tags?: string[]
  }
}

export interface CompleteExclusiveResponse {
  status: string
}

export interface ActiveExclusiveResponse {
  exclusive_session: ExclusiveSessionResponse | null
}

// Exclusive Session API Functions
export async function activateExclusive(request: ActivateExclusiveRequest): Promise<ActivateExclusiveResponse> {
  const data = await fetchAPI<unknown>('/v1/exclusive/activate', {
    method: 'POST',
    body: JSON.stringify(request),
  })
  return validateResponse(ActivateExclusiveResponseSchema, data, '/v1/exclusive/activate') as unknown as ActivateExclusiveResponse
}

export async function completeExclusive(request: CompleteExclusiveRequest): Promise<CompleteExclusiveResponse> {
  // Complete response is simple, no schema needed for MVP
  return fetchAPI<CompleteExclusiveResponse>('/v1/exclusive/complete', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function getActiveExclusive(): Promise<ActiveExclusiveResponse> {
  const data = await fetchAPI<unknown>('/v1/exclusive/active')
  return validateResponse(ActiveExclusiveResponseSchema, data, '/v1/exclusive/active') as unknown as ActiveExclusiveResponse
}

// Location Check
export interface LocationCheckResponse {
  in_charger_radius: boolean
  nearest_charger_id?: string
  distance_m?: number
}

export async function checkLocation(lat: number, lng: number): Promise<LocationCheckResponse> {
  const data = await fetchAPI<unknown>(`/v1/drivers/location/check?lat=${lat}&lng=${lng}`)
  return validateResponse(LocationCheckResponseSchema, data, '/v1/drivers/location/check') as unknown as LocationCheckResponse
}

// React Query Hooks for Exclusive Sessions
export function useActivateExclusive() {
  return useMutation({
    mutationFn: activateExclusive,
  })
}

export function useCompleteExclusive() {
  return useMutation({
    mutationFn: completeExclusive,
  })
}

export function useActiveExclusive() {
  return useQuery({
    queryKey: ['active-exclusive'],
    queryFn: getActiveExclusive,
    refetchInterval: 30000, // Poll every 30 seconds
  })
}

export function useLocationCheck(lat: number | null, lng: number | null) {
  return useQuery({
    queryKey: ['location-check', lat, lng],
    queryFn: () => lat !== null && lng !== null ? checkLocation(lat, lng) : null,
    enabled: lat !== null && lng !== null,
    refetchInterval: 10000, // Check every 10 seconds
  })
}

// Merchants for Charger
export interface MerchantForCharger {
  id: string
  merchant_id: string
  place_id?: string  // Frontend expects place_id for MerchantSummary compatibility
  name: string
  lat: number
  lng: number
  address?: string
  phone?: string
  logo_url?: string
  photo_url?: string  // Also support photo_url
  photo_urls?: string[]
  category?: string
  types?: string[]  // Frontend expects types array
  is_primary?: boolean
  exclusive_title?: string
  exclusive_description?: string
  open_now?: boolean
  open_until?: string
  rating?: number
  user_rating_count?: number
  walk_time_s?: number
  walk_time_seconds?: number
  distance_m?: number
}

export async function apiGetMerchantsForCharger(
  chargerId: string,
  options?: { state?: 'pre-charge' | 'charging', open_only?: boolean }
): Promise<MerchantForCharger[]> {
  const params = new URLSearchParams({
    charger_id: chargerId,
    state: options?.state || 'charging',
  })
  if (options?.open_only) {
    params.append('open_only', 'true')
  }
  
  const data = await fetchAPI<unknown>(`/v1/drivers/merchants/open?${params.toString()}`)
  return data as MerchantForCharger[]
}

export function useMerchantsForCharger(
  chargerId: string | null,
  options?: { state?: 'pre-charge' | 'charging', open_only?: boolean }
) {
  return useQuery({
    queryKey: ['merchants-for-charger', chargerId, options?.state, options?.open_only],
    queryFn: () => chargerId ? apiGetMerchantsForCharger(chargerId, options) : [],
    enabled: chargerId !== null,
  })
}

