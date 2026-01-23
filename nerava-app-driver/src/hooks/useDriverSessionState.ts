// State management hook for driver session state (PRE_CHARGING | CHARGING_ACTIVE)
import { useState, useEffect, useCallback } from 'react'

export type DriverSessionState = 'PRE_CHARGING' | 'CHARGING_ACTIVE'

const STORAGE_KEY = 'nerava_driver_session_state'
const STORAGE_RADIUS_KEY = 'nerava_is_in_charger_radius'

/**
 * Hook to manage global driver session state
 * - PRE_CHARGING: User not within charger radius
 * - CHARGING_ACTIVE: User within charger radius
 * 
 * Persists to localStorage for session continuity
 */
export function useDriverSessionState() {
  const [state, setState] = useState<DriverSessionState>(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'PRE_CHARGING' || stored === 'CHARGING_ACTIVE') {
      return stored
    }
    // Default to CHARGING_ACTIVE for demo purposes
    return 'CHARGING_ACTIVE'
  })

  const [isInChargerRadius, setIsInChargerRadius] = useState<boolean>(() => {
    // Load from localStorage on mount
    const stored = localStorage.getItem(STORAGE_RADIUS_KEY)
    if (stored === 'true') return true
    if (stored === 'false') return false
    // Default based on state
    return state === 'CHARGING_ACTIVE'
  })

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, state)
  }, [state])

  // Persist radius state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_RADIUS_KEY, String(isInChargerRadius))
  }, [isInChargerRadius])

  // Note: Radius is synced in setChargingState callback, no effect needed

  const setChargingState = useCallback((newState: DriverSessionState) => {
    setState(newState)
    // Update radius based on state
    if (newState === 'CHARGING_ACTIVE') {
      setIsInChargerRadius(true)
    } else {
      setIsInChargerRadius(false)
    }
  }, [])

  // Mock function to toggle radius (for testing)
  const toggleRadius = useCallback(() => {
    setIsInChargerRadius((prev) => !prev)
  }, [])

  return {
    state,
    isInChargerRadius,
    setChargingState,
    toggleRadius, // For dev/testing
  }
}

