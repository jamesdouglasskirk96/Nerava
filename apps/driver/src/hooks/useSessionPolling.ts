import { useState, useRef, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useVisibilityAwareInterval } from './usePageVisibility'
import { pollChargingSession, useTeslaStatus } from '../services/api'
import type { PollSessionResponse } from '../services/api'

interface SessionPollingState {
  isActive: boolean
  sessionId: string | null
  durationMinutes: number
  kwhDelivered: number | null
  lastIncentive: { amountCents: number } | null
  pollError: string | null
}

export function useSessionPolling() {
  const queryClient = useQueryClient()
  const { data: teslaStatus } = useTeslaStatus()
  const isAuthenticated = !!localStorage.getItem('access_token')
  const isTeslaConnected = teslaStatus?.connected === true

  const [state, setState] = useState<SessionPollingState>({
    isActive: false,
    sessionId: null,
    durationMinutes: 0,
    kwhDelivered: null,
    lastIncentive: null,
    pollError: null,
  })

  const wasActiveRef = useRef(false)
  const consecutiveErrorsRef = useRef(0)
  const deviceCoordsRef = useRef<{ lat: number; lng: number } | null>(null)

  // Continuously track device GPS for inclusion in poll requests
  const watchIdRef = useRef<number | null>(null)
  if (watchIdRef.current === null && typeof navigator !== 'undefined' && navigator.geolocation) {
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        deviceCoordsRef.current = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        }
      },
      () => {
        // Location unavailable — polls will proceed without device coords
      },
      { enableHighAccuracy: true, maximumAge: 30000 }
    )
  }

  const pollMutation = useMutation({
    mutationFn: () => {
      const coords = deviceCoordsRef.current
      return pollChargingSession(coords?.lat, coords?.lng)
    },
    onSuccess: (result: PollSessionResponse) => {
      if (result.error) {
        consecutiveErrorsRef.current += 1

        // If we thought a session was active but polls are failing,
        // keep showing active but track the error so the user can manually end
        if (wasActiveRef.current) {
          setState((prev) => ({
            ...prev,
            pollError: result.error || 'poll_failed',
          }))
          return
        }

        // Not tracking an active session — ignore poll errors (e.g. no_tesla_connection)
        return
      }

      // Successful poll — clear error state
      consecutiveErrorsRef.current = 0
      const wasActive = wasActiveRef.current

      if (result.session_active) {
        wasActiveRef.current = true
        setState({
          isActive: true,
          sessionId: result.session_id || null,
          durationMinutes: result.duration_minutes || 0,
          kwhDelivered: result.kwh_delivered ?? null,
          lastIncentive: null,
          pollError: null,
        })
      } else {
        wasActiveRef.current = false

        // Session just ended
        if (wasActive && result.session_ended) {
          // Invalidate session list + wallet to pick up new data
          queryClient.invalidateQueries({ queryKey: ['charging-sessions'] })
          queryClient.invalidateQueries({ queryKey: ['wallet'] })

          setState({
            isActive: false,
            sessionId: null,
            durationMinutes: 0,
            kwhDelivered: null,
            lastIncentive: result.incentive_granted
              ? { amountCents: result.incentive_amount_cents || 0 }
              : null,
            pollError: null,
          })
        } else {
          setState((prev) => ({
            ...prev,
            isActive: false,
            sessionId: null,
            durationMinutes: 0,
            kwhDelivered: null,
            pollError: null,
          }))
        }
      }
    },
  })

  const poll = useCallback(() => {
    if (!pollMutation.isPending) {
      pollMutation.mutate()
    }
  }, [pollMutation])

  // Poll every 30s (was 60s) for faster detection
  useVisibilityAwareInterval(poll, 30_000, isAuthenticated && isTeslaConnected)

  const clearIncentive = useCallback(() => {
    setState((prev) => ({ ...prev, lastIncentive: null }))
  }, [])

  return { ...state, clearIncentive }
}
