import { Zap, Clock, Battery } from 'lucide-react'
import type { ChargingSession } from '../../services/api'

interface SessionCardProps {
  session: ChargingSession
}

export function SessionCard({ session }: SessionCardProps) {
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
    <div className="flex items-center gap-3 bg-[#F7F8FA] rounded-card border border-[#E4E6EB] p-4">
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
          {duration > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {duration} min
            </span>
          )}
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

      {/* Incentive badge */}
      {incentive && incentive.amount_cents > 0 && (
        <span className="flex-shrink-0 px-2.5 py-1 bg-green-50 border border-green-200 rounded-full text-xs font-semibold text-green-700">
          +${(incentive.amount_cents / 100).toFixed(2)}
        </span>
      )}
    </div>
  )
}
