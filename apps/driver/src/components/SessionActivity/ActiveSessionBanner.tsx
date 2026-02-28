import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { endChargingSession } from '../../services/api'

interface ActiveSessionBannerProps {
  sessionId: string | null
  durationMinutes: number
  kwhDelivered: number | null
  onTap: () => void
  onSessionEnded?: () => void
  merchantName?: string
}

export function ActiveSessionBanner({ sessionId, durationMinutes, kwhDelivered, onTap, onSessionEnded, merchantName }: ActiveSessionBannerProps) {
  const timeLabel = durationMinutes > 0 ? `${durationMinutes} min` : 'Just started'
  const [confirmEnd, setConfirmEnd] = useState(false)
  const queryClient = useQueryClient()

  const endMutation = useMutation({
    mutationFn: () => {
      if (!sessionId) throw new Error('No session to end')
      return endChargingSession(sessionId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charging-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
      setConfirmEnd(false)
      onSessionEnded?.()
    },
    onError: () => {
      setConfirmEnd(false)
    },
  })

  return (
    <div className="w-full bg-[#1877F2] text-white flex-shrink-0">
      <div className="flex items-center justify-between px-4 py-2.5">
        <button onClick={onTap} className="flex items-center gap-2 flex-1 min-w-0">
          {/* Pulsing charging dot */}
          <span className="relative flex h-2 w-2 flex-shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
          </span>
          <span className="font-medium text-sm truncate">
            {merchantName || 'Charging'}
          </span>
          <span className="text-sm font-medium flex-shrink-0">
            {timeLabel}
            {kwhDelivered != null ? ` · ${kwhDelivered.toFixed(1)} kWh` : ''}
          </span>
        </button>

        {/* End Session button */}
        {sessionId && !confirmEnd && (
          <button
            onClick={(e) => { e.stopPropagation(); setConfirmEnd(true) }}
            className="ml-3 px-3 py-1 text-xs font-medium bg-white/20 rounded-full hover:bg-white/30 transition-colors flex-shrink-0"
          >
            End
          </button>
        )}

        {/* Confirm prompt */}
        {confirmEnd && (
          <div className="ml-3 flex items-center gap-2 flex-shrink-0">
            <button
              onClick={(e) => { e.stopPropagation(); endMutation.mutate() }}
              disabled={endMutation.isPending}
              className="px-3 py-1 text-xs font-semibold bg-red-500 rounded-full hover:bg-red-600 transition-colors disabled:opacity-50"
            >
              {endMutation.isPending ? 'Ending…' : 'Confirm'}
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setConfirmEnd(false) }}
              className="px-2 py-1 text-xs font-medium bg-white/20 rounded-full hover:bg-white/30 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
