import { useQuery, useMutation } from '@tanstack/react-query'
import type {
  CaptureIntentRequest,
  CaptureIntentResponse,
  MerchantDetailsResponse,
  WalletActivateRequest,
  WalletActivateResponse,
  ClusterResponse,
  ActivateExclusiveRequest,
  ActivateExclusiveResponse,
  ExclusiveSessionResponse,
} from '../types'
import {
  captureIntentMock,
  getMerchantDetailsMock,
  activateExclusiveMock,
} from '../mock/mockApi'
import type { MockCaptureIntentRequest } from '../mock/types'

// Detect API base URL: use env var if set, otherwise detect from hostname
function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // If running on production domain, use production API
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname.includes('nerava.network') || hostname.includes('nerava.app')) {
      return 'https://api.nerava.network'
    }
  }
  // Default to localhost for local development
  return 'http://localhost:8001'
}

const API_BASE_URL = getApiBaseUrl()

/**
 * Resolve a photo URL to an absolute URL.
 * If the URL is relative (starts with /), prepend the API base URL.
 * If already absolute, return as-is.
 */
export function resolvePhotoUrl(url: string | null | undefined): string | null {
  if (!url) return null
  // If it's a relative URL starting with /, prepend API base
  if (url.startsWith('/')) {
    const resolved = `${API_BASE_URL}${url}`
    // Log Asadas Grill photo resolution for debugging (dev only)
    if (import.meta.env.DEV && (url.includes('asadas') || url.includes('Asadas'))) {
      console.log(`[resolvePhotoUrl] Resolved Asadas Grill photo:`, { original: url, resolved, apiBase: API_BASE_URL })
    }
    return resolved
  }
  // If it's already absolute (http/https), return as-is
  return url
}

// Check if mock mode is enabled - default to backend mode unless explicitly set
export function isMockMode(): boolean {
  return import.meta.env.VITE_MOCK_MODE === 'true'
}

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

export async function fetchAPI<T>(endpoint: string, options?: RequestInit, retryOn401 = true): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const token = localStorage.getItem('access_token')
  
  const headers = new Headers(options?.headers)
  headers.set('Content-Type', 'application/json')
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  
  console.log('[API] Fetching:', url, { method: options?.method || 'GET', headers: Object.fromEntries(headers.entries()) })
  console.log('[API] API_BASE_URL:', API_BASE_URL)
  
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
    console.error('[API] Error type:', error?.constructor?.name)
    console.error('[API] Error details:', {
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      url,
      apiBaseUrl: API_BASE_URL,
    })
    // Re-throw ApiError as-is, wrap other errors
    if (error instanceof ApiError) {
      console.error('[API] Throwing ApiError:', error.status, error.code, error.message)
      throw error
    }
    // Network errors or other fetch failures
    const errorMessage = error instanceof Error 
      ? error.message 
      : String(error) || 'Network error'
    const apiError = new ApiError(0, 'network_error', errorMessage)
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
      return await fetchAPI<CaptureIntentResponse>('/v1/intent/capture', {
        method: 'POST',
        body: JSON.stringify(request),
      })
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
      // Use mock API if merchantId starts with "mock_" or if mock mode is enabled
      if (merchantId && (isMockMode() || merchantId.startsWith('mock_'))) {
        return await getMerchantDetailsMock(merchantId, sessionId)
      }
      // Use real API
      const params = sessionId ? `?session_id=${sessionId}` : ''
      return fetchAPI<MerchantDetailsResponse>(`/v1/merchants/${merchantId}${params}`)
    },
    enabled: merchantId !== null,
  })
}

// Wallet Activate
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

// Party Cluster
export function usePartyCluster(clusterId: string | null) {
  return useQuery({
    queryKey: ['party-cluster', clusterId],
    queryFn: async () => {
      const params = clusterId ? `?cluster_id=${clusterId}` : ''
      return fetchAPI<ClusterResponse>(`/v1/pilot/party/cluster${params}`)
    },
    enabled: true, // Always enabled, clusterId can be null (will use default)
  })
}

// Exclusive Activate
export function useExclusiveActivate() {
  return useMutation({
    mutationFn: async (request: ActivateExclusiveRequest) => {
      return fetchAPI<ActivateExclusiveResponse>('/v1/exclusive/activate', {
        method: 'POST',
        body: JSON.stringify(request),
      })
    },
  })
}

// Exclusive Complete
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

export function useExclusiveComplete() {
  return useMutation({
    mutationFn: async (request: CompleteExclusiveRequest) => {
      return fetchAPI<CompleteExclusiveResponse>('/v1/exclusive/complete', {
        method: 'POST',
        body: JSON.stringify(request),
      })
    },
  })
}

// Get Active Exclusive
export interface ActiveExclusiveResponse {
  exclusive_session: ExclusiveSessionResponse | null
}

export function useActiveExclusive() {
  return useQuery({
    queryKey: ['active-exclusive'],
    queryFn: async () => {
      return fetchAPI<ActiveExclusiveResponse>('/v1/exclusive/active')
    },
    refetchInterval: 60000, // Poll every minute
    enabled: true, // Always enabled when component mounts
  })
}

// Favorites
export interface FavoriteResponse {
  ok: boolean
  is_favorite: boolean
}

export interface FavoritesListResponse {
  favorites: Array<{
    merchant_id: string
    name: string
    category?: string
    photo_url?: string
  }>
}

export function useFavorites() {
  return useQuery({
    queryKey: ['favorites'],
    queryFn: async () => {
      return fetchAPI<FavoritesListResponse>('/v1/merchants/favorites')
    },
  })
}

export function useAddFavorite() {
  return useMutation({
    mutationFn: async (merchantId: string) => {
      return fetchAPI<FavoriteResponse>(`/v1/merchants/${merchantId}/favorite`, {
        method: 'POST',
      })
    },
  })
}

export function useRemoveFavorite() {
  return useMutation({
    mutationFn: async (merchantId: string) => {
      return fetchAPI<FavoriteResponse>(`/v1/merchants/${merchantId}/favorite`, {
        method: 'DELETE',
      })
    },
  })
}

// Share
export interface ShareLinkResponse {
  url: string
  title: string
  description: string
}

export function useShareLink(merchantId: string | null) {
  return useQuery({
    queryKey: ['share-link', merchantId],
    queryFn: async () => {
      if (!merchantId) throw new Error('Merchant ID required')
      return fetchAPI<ShareLinkResponse>(`/v1/merchants/${merchantId}/share-link`)
    },
    enabled: !!merchantId,
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

