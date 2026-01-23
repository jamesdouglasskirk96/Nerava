/**
 * Hook that determines UI state based on location and charger discovery API
 */
import { useState, useEffect } from 'react'
import { useGeolocation } from './useGeolocation'
import { getChargerDiscovery, type DiscoveryResponse } from '../api/chargers'

export function useChargerState() {
  const geo = useGeolocation()
  const [data, setData] = useState<DiscoveryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Only fetch when location is available and not loading
    if (geo.lat && geo.lng && !geo.loading) {
      setLoading(true)
      setError(null)

      getChargerDiscovery(geo.lat, geo.lng)
        .then((response) => {
          setData(response)
          setLoading(false)
        })
        .catch((err) => {
          console.error('Failed to fetch charger discovery:', err)
          setError(err.message)
          setLoading(false)
        })
    } else if (!geo.loading && (!geo.lat || !geo.lng)) {
      // Location not available
      setLoading(false)
    }
  }, [geo.lat, geo.lng, geo.loading])

  return {
    loading: loading || geo.loading,
    error,
    // THE CRITICAL STATE DECISION:
    showCharging: data?.within_radius ?? false,
    nearestChargerId: data?.nearest_charger_id ?? null,
    chargers: data?.chargers ?? []
  }
}

