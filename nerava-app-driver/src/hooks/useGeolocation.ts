/**
 * Geolocation hook with periodic polling
 * Calculates distance to charger and merchant locations
 */
import { useState, useEffect, useCallback } from 'react'

// Canyon Ridge Supercharger coordinates (Asadas Grill cluster)
const CHARGER_LOCATION = {
  lat: 30.4027,
  lng: -97.6719,
}

// Asadas Grill coordinates
const ASADAS_GRILL_LOCATION = {
  lat: 30.4028,
  lng: -97.6719,
}

// Mock location for development - set to null to use real GPS
// Change these values to test different scenarios:
// - Near charger: { lat: 30.4027, lng: -97.6719 }
// - Far from charger: { lat: 30.5, lng: -97.7 }
// - Near merchant: { lat: 30.4028, lng: -97.6719 }
let MOCK_LOCATION: { lat: number; lng: number } | null = null

// Export function to set mock location for testing
export function setMockLocation(location: { lat: number; lng: number } | null) {
  MOCK_LOCATION = location
  console.log('[Geolocation] Mock location set to:', location)
}

// Export function to get current mock location
export function getMockLocation() {
  return MOCK_LOCATION
}

// Expose to window for easy console testing
if (typeof window !== 'undefined') {
  ;(window as any).setMockLocation = setMockLocation
  ;(window as any).getMockLocation = getMockLocation
  ;(window as any).CHARGER_LOCATION = CHARGER_LOCATION
  ;(window as any).MERCHANT_LOCATION = ASADAS_GRILL_LOCATION

  // Check URL params for mock location (e.g., ?mock=charger or ?mock=merchant or ?mock=far)
  const urlParams = new URLSearchParams(window.location.search)
  const mockParam = urlParams.get('mock')
  if (mockParam === 'charger') {
    MOCK_LOCATION = { lat: 30.4027, lng: -97.6719 }
    console.log('[Geolocation] Mock location set via URL param: near charger')
  } else if (mockParam === 'merchant') {
    MOCK_LOCATION = { lat: 30.4028, lng: -97.6719 }
    console.log('[Geolocation] Mock location set via URL param: near merchant')
  } else if (mockParam === 'far') {
    MOCK_LOCATION = { lat: 30.5, lng: -97.7 }
    console.log('[Geolocation] Mock location set via URL param: far away')
  }

  console.log('[Geolocation] Testing helpers available:')
  console.log('  URL params: ?mock=charger | ?mock=merchant | ?mock=far')
  console.log('  Console: setMockLocation({ lat, lng })')
  console.log('')
  console.log('Test scenarios:')
  console.log('  - Near charger (can activate): ?mock=charger')
  console.log('  - Near merchant (can verify): ?mock=merchant')
  console.log('  - Far away: ?mock=far')
}

export interface GeolocationState {
  lat: number | null
  lng: number | null
  accuracy: number | null
  error: string | null
  loading: boolean
  distanceToCharger: number | null  // meters
  distanceToMerchant: number | null // meters
  isNearCharger: boolean  // within 400m
  isNearMerchant: boolean // within 40m
  lastUpdated: Date | null
}

/**
 * Calculate distance between two coordinates using Haversine formula
 * Returns distance in meters
 */
function calculateDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const R = 6371000 // Earth's radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

const CHARGER_RADIUS_M = 400  // Must be within 400m of charger to activate
const MERCHANT_RADIUS_M = 40  // Must be within 40m of merchant to verify visit

export function useGeolocation(pollingInterval = 5000): GeolocationState & { refresh: () => void } {
  const [state, setState] = useState<GeolocationState>({
    lat: null,
    lng: null,
    accuracy: null,
    error: null,
    loading: true,
    distanceToCharger: null,
    distanceToMerchant: null,
    isNearCharger: false,
    isNearMerchant: false,
    lastUpdated: null,
  })

  const updateLocation = useCallback(() => {
    // Use mock location if set (for development/testing)
    if (MOCK_LOCATION) {
      const distanceToCharger = calculateDistance(
        MOCK_LOCATION.lat,
        MOCK_LOCATION.lng,
        CHARGER_LOCATION.lat,
        CHARGER_LOCATION.lng
      )
      const distanceToMerchant = calculateDistance(
        MOCK_LOCATION.lat,
        MOCK_LOCATION.lng,
        ASADAS_GRILL_LOCATION.lat,
        ASADAS_GRILL_LOCATION.lng
      )

      setState({
        lat: MOCK_LOCATION.lat,
        lng: MOCK_LOCATION.lng,
        accuracy: 10,
        error: null,
        loading: false,
        distanceToCharger,
        distanceToMerchant,
        isNearCharger: distanceToCharger <= CHARGER_RADIUS_M,
        isNearMerchant: distanceToMerchant <= MERCHANT_RADIUS_M,
        lastUpdated: new Date(),
      })
      console.log('[Geolocation] Using mock location:', {
        ...MOCK_LOCATION,
        distanceToCharger: Math.round(distanceToCharger),
        distanceToMerchant: Math.round(distanceToMerchant),
        isNearCharger: distanceToCharger <= CHARGER_RADIUS_M,
        isNearMerchant: distanceToMerchant <= MERCHANT_RADIUS_M,
      })
      return
    }

    // Use real geolocation
    if (!navigator.geolocation) {
      setState(prev => ({
        ...prev,
        error: 'Geolocation is not supported by your browser',
        loading: false,
      }))
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords
        const distanceToCharger = calculateDistance(
          latitude,
          longitude,
          CHARGER_LOCATION.lat,
          CHARGER_LOCATION.lng
        )
        const distanceToMerchant = calculateDistance(
          latitude,
          longitude,
          ASADAS_GRILL_LOCATION.lat,
          ASADAS_GRILL_LOCATION.lng
        )

        setState({
          lat: latitude,
          lng: longitude,
          accuracy,
          error: null,
          loading: false,
          distanceToCharger,
          distanceToMerchant,
          isNearCharger: distanceToCharger <= CHARGER_RADIUS_M,
          isNearMerchant: distanceToMerchant <= MERCHANT_RADIUS_M,
          lastUpdated: new Date(),
        })
        console.log('[Geolocation] Real location:', {
          latitude,
          longitude,
          distanceToCharger: Math.round(distanceToCharger),
          distanceToMerchant: Math.round(distanceToMerchant),
        })
      },
      (error) => {
        let errorMessage = error.message
        // Provide more helpful error messages
        if (error.code === 1) {
          errorMessage = 'Location permission denied. Please allow location access in browser settings.'
        } else if (error.code === 2) {
          errorMessage = 'Location unavailable. Please check GPS is enabled.'
        } else if (error.code === 3) {
          errorMessage = 'Location request timed out. Try using mock location in console.'
        }
        console.error('[Geolocation] Error:', error.code, errorMessage)
        console.log('[Geolocation] Tip: Use setMockLocation({ lat: 30.4027, lng: -97.6719 }) to simulate being near the charger')
        setState(prev => ({
          ...prev,
          error: errorMessage,
          loading: false,
        }))
      },
      {
        enableHighAccuracy: false, // Try with lower accuracy first (faster)
        timeout: 30000, // Increase timeout to 30 seconds
        maximumAge: 60000, // Allow cached positions up to 1 minute old
      }
    )
  }, [])

  useEffect(() => {
    // Initial location fetch
    updateLocation()

    // Set up polling interval (every 5 seconds by default)
    const intervalId = setInterval(updateLocation, pollingInterval)

    return () => clearInterval(intervalId)
  }, [updateLocation, pollingInterval])

  return {
    ...state,
    refresh: updateLocation,
  }
}

// Export constants for use in other components
export { CHARGER_LOCATION, ASADAS_GRILL_LOCATION, CHARGER_RADIUS_M, MERCHANT_RADIUS_M }
