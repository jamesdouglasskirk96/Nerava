// State machine hook for driver app states
import { useState, useEffect, useCallback } from 'react'

export type ChargingState = 'PRE_CHARGING' | 'CHARGING_ACTIVE' | 'EXCLUSIVE_ACTIVE' | 'COMPLETE'

/**
 * Hook to manage driver app state machine:
 * - PRE_CHARGING: Not near charger, show charger-first routing
 * - CHARGING_ACTIVE: Near charger, show merchant exclusives
 * - EXCLUSIVE_ACTIVE: Exclusive session active, show only active exclusive UI
 * - COMPLETE: Exclusive completed, show preferences prompt
 */
export function useChargingState() {
  const [state, setState] = useState<ChargingState>(() => {
    // Load from localStorage
    const stored = localStorage.getItem('nerava_charging_state')
    if (stored && ['PRE_CHARGING', 'CHARGING_ACTIVE', 'EXCLUSIVE_ACTIVE', 'COMPLETE'].includes(stored)) {
      return stored as ChargingState
    }
    return 'PRE_CHARGING' // Default to pre-charging
  })

  // Persist state changes
  useEffect(() => {
    localStorage.setItem('nerava_charging_state', state)
  }, [state])

  const transitionTo = useCallback((newState: ChargingState) => {
    setState(newState)
  }, [])

  return {
    state,
    transitionTo,
    isPreCharging: state === 'PRE_CHARGING',
    isChargingActive: state === 'CHARGING_ACTIVE',
    isExclusiveActive: state === 'EXCLUSIVE_ACTIVE',
    isComplete: state === 'COMPLETE',
  }
}

