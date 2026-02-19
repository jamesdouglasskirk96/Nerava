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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'

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
          const refreshResponse = await fetch(`${API_BASE_URL}/v1/auth/refresh`, {
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
        // Don't log 401 errors when retryOn401 is false (expected for anonymous users)
        if (retryOn401) {
          console.error('[API] No refresh token available for 401 retry')
        }
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
    // Don't log 401 errors when retryOn401 is false (expected for anonymous users)
    if (!(error instanceof ApiError && error.status === 401 && !retryOn401)) {
      console.error('[API] Fetch error:', error)
    }
    // Re-throw ApiError as-is, wrap other errors
    if (error instanceof ApiError) {
      // Only log non-401 errors or 401s where retry was attempted
      if (!(error.status === 401 && !retryOn401)) {
        console.error('[API] Throwing ApiError:', error.status, error.code, error.message)
      }
      throw error
    }
    // Network errors or other fetch failures
    const apiError = new ApiError(0, 'network_error', error instanceof Error ? error.message : 'Network error')
    console.error('[API] Throwing wrapped ApiError:', apiError.status, apiError.code, apiError.message)
    throw apiError
  }
}

// Intent Capture - with module-level cache and pending request deduplication
// This provides multiple layers of protection against infinite fetches
interface IntentCache {
  key: string
  data: CaptureIntentResponse
  timestamp: number
}
let intentCache: IntentCache | null = null
let pendingIntentRequest: Promise<CaptureIntentResponse> | null = null
let pendingIntentKey: string | null = null
const INTENT_CACHE_TTL_MS = 60000 // 60 seconds cache TTL

// AGGRESSIVE: Global flag to completely stop fetches after first success
let hasSuccessfullyFetched = false
let lastFetchTimestamp = 0
const MIN_FETCH_INTERVAL_MS = 5000 // Minimum 5 seconds between fetches

export function useIntentCapture(request: CaptureIntentRequest | null) {
  // Use stable queryKey with ROUNDED coordinates to prevent refetch on GPS fluctuation
  // GPS watchPosition returns slightly different values each time - round to 4 decimal places (~11m precision)
  const roundedLat = request ? Math.round(request.lat * 10000) / 10000 : null
  const roundedLng = request ? Math.round(request.lng * 10000) / 10000 : null
  const cacheKey = request ? `${roundedLat},${roundedLng}` : ''
  const queryKey = request
    ? ['intent-capture', roundedLat, roundedLng]
    : ['intent-capture', null]

  return useQuery({
    queryKey,
    queryFn: async () => {
      const now = Date.now()

      // AGGRESSIVE: Rate limit - prevent fetches within 5 seconds of last fetch
      if (hasSuccessfullyFetched && (now - lastFetchTimestamp) < MIN_FETCH_INTERVAL_MS) {
        console.log('[API] Intent capture rate limited (too soon after last fetch)')
        if (intentCache) {
          return intentCache.data
        }
        // If no cache but rate limited, throw to prevent infinite loops
        throw new Error('Rate limited - please wait before retrying')
      }

      // Check module-level cache first - prevents unnecessary API calls
      if (intentCache && intentCache.key === cacheKey && (now - intentCache.timestamp) < INTENT_CACHE_TTL_MS) {
        console.log('[API] Intent capture using cached response (cache hit)')
        return intentCache.data
      }

      // Check if there's already a pending request for the same key - deduplicate
      if (pendingIntentRequest && pendingIntentKey === cacheKey) {
        console.log('[API] Intent capture reusing pending request (deduplication)')
        return pendingIntentRequest
      }

      // Create the actual fetch function
      const doFetch = async (): Promise<CaptureIntentResponse> => {
        if (isMockMode() && request) {
          // Use mock API in mock mode
          return await captureIntentMock(request as MockCaptureIntentRequest)
        }
        // Use real API - disable token refresh for anonymous requests
        // This endpoint supports optional authentication
        const hasToken = !!localStorage.getItem('access_token')
        const data = await fetchAPI<unknown>('/v1/intent/capture', {
          method: 'POST',
          body: JSON.stringify(request),
        }, hasToken) // Only retry token refresh if user has a token

        // Debug: Log raw API response before validation
        console.log('[API] Raw intent capture response:', {
          merchants_count: Array.isArray((data as any)?.merchants) ? (data as any).merchants.length : 'not array',
          merchants: (data as any)?.merchants,
          charger_summary: (data as any)?.charger_summary,
          confidence_tier: (data as any)?.confidence_tier,
        })

        // Validate response schema
        const validated = validateResponse(CaptureIntentResponseSchema, data, '/v1/intent/capture') as unknown as CaptureIntentResponse

        // Debug: Log validated response
        console.log('[API] Validated intent capture response:', {
          merchants_count: validated.merchants?.length || 0,
          merchants: validated.merchants,
          charger_summary: validated.charger_summary,
          confidence_tier: validated.confidence_tier,
        })

        return validated
      }

      // Set pending request state and execute
      pendingIntentKey = cacheKey
      lastFetchTimestamp = now // Track fetch time for rate limiting
      pendingIntentRequest = doFetch().then(validated => {
        // Store in module-level cache on success
        intentCache = { key: cacheKey, data: validated, timestamp: now }
        hasSuccessfullyFetched = true // Mark as successfully fetched
        lastFetchTimestamp = Date.now() // Update to completion time
        return validated
      }).finally(() => {
        // Clear pending state when done
        if (pendingIntentKey === cacheKey) {
          pendingIntentRequest = null
          pendingIntentKey = null
        }
      })

      return pendingIntentRequest
    },
    enabled: request !== null,
    staleTime: 60000, // Data is fresh for 1 minute - prevents refetching
    gcTime: 300000, // Keep in cache for 5 minutes
    retry: false, // Don't retry on error
    refetchOnMount: false, // Don't refetch on mount - CRITICAL for preventing loops
    refetchOnReconnect: false, // Don't refetch on reconnect
    refetchOnWindowFocus: false, // Don't refetch on window focus
    refetchInterval: false, // No automatic refetching
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
  merchant_place_id?: string | null
  charger_id: string
  charger_place_id?: string
  intent_session_id?: string
  lat: number | null  // V3: null allowed when location unavailable
  lng: number | null  // V3: null allowed when location unavailable
  accuracy_m?: number
  // NEW: Intent capture fields (V3)
  intent?: 'eat' | 'work' | 'quick-stop'
  party_size?: number
  needs_power_outlet?: boolean
  is_to_go?: boolean
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

export async function getActiveExclusive(): Promise<ActiveExclusiveResponse | null> {
  // Check if user is authenticated before making request
  const hasToken = !!localStorage.getItem('access_token')
  if (!hasToken) {
    // Return null for anonymous users (no active exclusive)
    return { exclusive_session: null }
  }
  
  try {
    // Disable token refresh retry - if auth fails, user is not authenticated
    const data = await fetchAPI<unknown>('/v1/exclusive/active', undefined, false)
    return validateResponse(ActiveExclusiveResponseSchema, data, '/v1/exclusive/active') as unknown as ActiveExclusiveResponse
  } catch (error) {
    // Handle 401 gracefully - user is not authenticated, so no active exclusive
    // This is expected for anonymous users, so don't log as error
    if (error instanceof ApiError && error.status === 401) {
      // Silently return null (no active exclusive for unauthenticated users)
      return { exclusive_session: null }
    }
    // Log and re-throw other errors
    console.error('[API] Error fetching active exclusive:', error)
    throw error
  }
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
  // Check authentication state - handle 401 gracefully in getActiveExclusive
  // Query will run but return null for anonymous users (no error thrown)
  return useQuery<ActiveExclusiveResponse | null>({
    queryKey: ['active-exclusive'],
    queryFn: getActiveExclusive,
    retry: false, // Don't retry on error (401 is expected for anonymous users)
    refetchInterval: () => {
      // Only poll if we have a token (check on each interval)
      const hasToken = !!localStorage.getItem('access_token')
      return hasToken ? 30000 : false
    },
    // Note: onError was removed in React Query v5, errors are handled via the error state
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

// Verify Visit - generates incremental verification code for merchant
export interface VerifyVisitRequest {
  exclusive_session_id: string
  lat?: number
  lng?: number
}

export interface VerifyVisitResponse {
  status: string // "VERIFIED" or "ALREADY_VERIFIED"
  verification_code: string // e.g., "ATX-ASADAS-023"
  visit_number: number
  merchant_name: string
  verified_at: string
}

export async function verifyVisit(request: VerifyVisitRequest): Promise<VerifyVisitResponse> {
  return fetchAPI<VerifyVisitResponse>('/v1/exclusive/verify', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export function useVerifyVisit() {
  return useMutation({
    mutationFn: verifyVisit,
  })
}

// Amenity Votes API
export interface AmenityVoteRequest {
  vote_type: 'up' | 'down'
}

export interface AmenityVoteResponse {
  ok: boolean
  upvotes: number
  downvotes: number
}

export async function voteAmenity(
  merchantId: string,
  amenity: 'bathroom' | 'wifi',
  voteType: 'up' | 'down'
): Promise<AmenityVoteResponse> {
  return fetchAPI<AmenityVoteResponse>(
    `/v1/merchants/${merchantId}/amenities/${amenity}/vote`,
    {
      method: 'POST',
      body: JSON.stringify({ vote_type: voteType }),
    }
  )
}

export function useVoteAmenity() {
  return useMutation({
    mutationFn: ({ merchantId, amenity, voteType }: { merchantId: string; amenity: 'bathroom' | 'wifi'; voteType: 'up' | 'down' }) =>
      voteAmenity(merchantId, amenity, voteType),
  })
}

// API client object for convenience
export const api = {
  get: <T>(endpoint: string, retryOn401 = true): Promise<T> => {
    return fetchAPI<T>(endpoint, { method: 'GET' }, retryOn401)
  },
  post: <T>(endpoint: string, data?: any, retryOn401 = true): Promise<T> => {
    return fetchAPI<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }, retryOn401)
  },
  put: <T>(endpoint: string, data?: any, retryOn401 = true): Promise<T> => {
    return fetchAPI<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }, retryOn401)
  },
  delete: <T>(endpoint: string, retryOn401 = true): Promise<T> => {
    return fetchAPI<T>(endpoint, { method: 'DELETE' }, retryOn401)
  },
}
