/**
 * API client for charger discovery endpoint
 */

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

export interface NearbyMerchant {
  place_id: string
  name: string
  photo_url: string
  distance_m: number
  walk_time_min: number
  has_exclusive: boolean
}

export interface DiscoveryCharger {
  id: string
  name: string
  address: string
  lat: number
  lng: number
  distance_m: number
  drive_time_min: number
  network: string
  stalls: number
  kw: number
  photo_url: string
  nearby_merchants: NearbyMerchant[]
}

export interface DiscoveryResponse {
  within_radius: boolean
  nearest_charger_id: string | null
  nearest_distance_m: number
  radius_m: number
  chargers: DiscoveryCharger[]
}

/**
 * Get charger discovery data for a given location
 */
export async function getChargerDiscovery(lat: number, lng: number): Promise<DiscoveryResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/chargers/discovery?lat=${lat}&lng=${lng}`)
  if (!response.ok) {
    throw new Error(`Discovery API failed: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Get charger by ID from discovery response
 * This is a helper function that searches the discovery response for a charger
 */
export function getChargerFromDiscovery(
  chargerId: string,
  discoveryResponse: DiscoveryResponse
): DiscoveryCharger | null {
  return discoveryResponse.chargers.find(c => c.id === chargerId) || null
}

