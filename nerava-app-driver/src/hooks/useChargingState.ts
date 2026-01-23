// Simple local state hook for charging state - no GPS/location logic
import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

export type ChargingState = 'charging' | 'pre-charging'

/**
 * Hook to get current charging state
 * Uses route path to determine state, or defaults to 'charging'
 * For dev: can be toggled via URL param ?state=pre-charging
 */
export function useChargingState(): ChargingState {
  const location = useLocation()
  const [state, setState] = useState<ChargingState>('charging')

  useEffect(() => {
    // Check URL param first
    const params = new URLSearchParams(location.search)
    const urlState = params.get('state')
    if (urlState === 'pre-charging') {
      setState('pre-charging')
      return
    }

    // Check route path
    if (location.pathname === '/pre-charging') {
      setState('pre-charging')
    } else {
      setState('charging')
    }
  }, [location.pathname, location.search])

  return state
}

