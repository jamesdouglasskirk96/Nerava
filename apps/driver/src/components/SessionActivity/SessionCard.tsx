import { useState } from 'react'
import { Zap, Clock, Battery, ChevronDown, ChevronUp, MapPin, Plug, Gauge, ShieldCheck, StopCircle } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { endChargingSession } from '../../services/api'
import type { ChargingSession } from '../../services/api'

interface SessionCardProps {
  session: ChargingSession
}

export function SessionCard({ session }: SessionCardProps) {
  const [expanded, setExpanded] = useState(false)
  const queryClient = useQueryClient()

  const endSessionMutation = useMutation({
    mutationFn: () => endChargingSession(session.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charging-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
    },
  })

  const date = session.session_start
    ? new Date(session.session_start.endsWith('Z') ? session.session_start : session.session_start + 'Z')
    : null

  const dateLabel = date
    ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : 'Unknown date'

  const timeLabel = date
    ? date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    : ''

  const networkLabel = session.charger_network || 'Unknown network'
  const duration = session.duration_minutes ?? 0
  const kwh = session.kwh_delivered != null ? session.kwh_delivered.toFixed(1) : null
  const batteryDelta =
    session.battery_start_pct != null && session.battery_end_pct != null
      ? session.battery_end_pct - session.battery_start_pct
      : null

  const incentive = session.incentive

  return (
    <div
      className="bg-[#F7F8FA] rounded-card border border-[#E4E6EB] overflow-hidden cursor-pointer active:bg-[#EDEEF0] transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-3 p-4">
        {/* Icon */}
        <div className="w-10 h-10 rounded-full bg-[#1877F2]/10 flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-[#1877F2]" />
        </div>

        {/* Details */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[#050505] truncate">{networkLabel}</p>
          <p className="text-xs text-[#656A6B]">
            {dateLabel}{timeLabel ? ` at ${timeLabel}` : ''}
          </p>
          <div className="flex items-center gap-3 mt-1 text-xs text-[#656A6B]">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {duration > 0 ? `${duration} min` : !session.session_end ? 'Charging…' : '< 1 min'}
            </span>
            {kwh && (
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                {kwh} kWh
              </span>
            )}
            {batteryDelta != null && batteryDelta > 0 && (
              <span className="flex items-center gap-1">
                <Battery className="w-3 h-3" />
                +{batteryDelta}%
              </span>
            )}
          </div>
        </div>

        {/* Incentive badge + expand indicator */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {incentive && incentive.amount_cents > 0 && (
            <span className="px-2.5 py-1 bg-green-50 border border-green-200 rounded-full text-xs font-semibold text-green-700">
              +${(incentive.amount_cents / 100).toFixed(2)}
            </span>
          )}
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-[#656A6B]" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[#656A6B]" />
          )}
        </div>
      </div>

      {/* Expanded detail section */}
      {expanded && (
        <div className="border-t border-[#E4E6EB] px-4 py-3 space-y-2.5 bg-white">
          {/* Duration */}
          <div className="flex items-center gap-2 text-xs text-[#656A6B]">
            <Clock className="w-3.5 h-3.5" />
            <span>
              {duration > 0
                ? `${duration} min total`
                : session.session_end
                  ? 'Less than 1 min'
                  : 'Still charging'}
              {timeLabel && ` • Started ${timeLabel}`}
            </span>
          </div>

          {/* Battery range */}
          {(session.battery_start_pct != null || session.battery_end_pct != null) && (
            <div className="flex items-center gap-2 text-xs text-[#656A6B]">
              <Battery className="w-3.5 h-3.5" />
              <span>
                {session.battery_start_pct != null ? `${session.battery_start_pct}%` : '—'}
                {session.battery_end_pct != null ? ` → ${session.battery_end_pct}%` : !session.session_end ? ' (charging…)' : ''}
                {batteryDelta != null && batteryDelta > 0 && (
                  <span className="text-green-600 font-medium"> (+{batteryDelta}%)</span>
                )}
              </span>
            </div>
          )}

          {/* Power */}
          {session.power_kw != null && session.power_kw > 0 && (
            <div className="flex items-center gap-2 text-xs text-[#656A6B]">
              <Gauge className="w-3.5 h-3.5" />
              <span>{session.power_kw} kW peak power</span>
            </div>
          )}

          {/* Connector type */}
          {session.connector_type && (
            <div className="flex items-center gap-2 text-xs text-[#656A6B]">
              <Plug className="w-3.5 h-3.5" />
              <span>{session.connector_type} connector</span>
            </div>
          )}

          {/* Location */}
          {session.lat != null && session.lng != null && (
            <div className="flex items-center gap-2 text-xs text-[#656A6B]">
              <MapPin className="w-3.5 h-3.5" />
              <a
                href={`https://maps.google.com/?q=${session.lat},${session.lng}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#1877F2] underline"
                onClick={(e) => e.stopPropagation()}
              >
                View on map
              </a>
            </div>
          )}

          {/* Verified status */}
          {session.verified && (
            <div className="flex items-center gap-2 text-xs text-green-600">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verified via Tesla API</span>
            </div>
          )}

          {/* End session button for active sessions */}
          {!session.session_end && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                endSessionMutation.mutate()
              }}
              disabled={endSessionMutation.isPending}
              className="w-full mt-1 py-2 px-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs font-medium flex items-center justify-center gap-1.5 hover:bg-red-100 transition-colors disabled:opacity-50"
            >
              <StopCircle className="w-3.5 h-3.5" />
              {endSessionMutation.isPending ? 'Ending…' : 'End Session'}
            </button>
          )}

          {/* Incentive details */}
          {incentive && incentive.amount_cents > 0 && (
            <div className="mt-2 pt-2 border-t border-[#E4E6EB]">
              <div className="flex items-center justify-between text-xs">
                <span className="text-[#656A6B]">Reward earned</span>
                <span className="font-semibold text-green-700">
                  ${(incentive.amount_cents / 100).toFixed(2)}
                </span>
              </div>
              <p className="text-xs text-[#656A6B] mt-0.5">
                Status: {incentive.status}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
