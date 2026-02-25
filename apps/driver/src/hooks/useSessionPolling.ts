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
  })

  const wasActiveRef = useRef(false)

  const pollMutation = useMutation({
    mutationFn: pollChargingSession,
    onSuccess: (result: PollSessionResponse) => {
      if (result.error) {
        // Tesla not connected or poll failed — stay idle
        return
      }

      const wasActive = wasActiveRef.current

      if (result.session_active) {
        wasActiveRef.current = true
        setState({
          isActive: true,
          sessionId: result.session_id || null,
          durationMinutes: result.duration_minutes || 0,
          kwhDelivered: result.kwh_delivered ?? null,
          lastIncentive: null,
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
          })
        } else {
          setState((prev) => ({
            ...prev,
            isActive: false,
            sessionId: null,
            durationMinutes: 0,
            kwhDelivered: null,
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

  useVisibilityAwareInterval(poll, 60_000, isAuthenticated && isTeslaConnected)

  const clearIncentive = useCallback(() => {
    setState((prev) => ({ ...prev, lastIncentive: null }))
  }, [])

  return { ...state, clearIncentive }
}
