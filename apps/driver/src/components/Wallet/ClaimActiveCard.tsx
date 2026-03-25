import { Zap, Clock, MapPin, ChevronRight, Gift } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { ExclusiveSessionResponse } from '../../services/api'

interface ClaimActiveCardProps {
  session: ExclusiveSessionResponse
  remainingSeconds: number
}

export function ClaimActiveCard({ session, remainingSeconds }: ClaimActiveCardProps) {
  const navigate = useNavigate()
  const minutes = Math.floor(remainingSeconds / 60)
  const seconds = remainingSeconds % 60

  const merchantName = session.merchant_name || 'Merchant'
  const chargerName = session.charger_name || 'Charger'
  const offerTitle = session.exclusive_title
  const walkMin = session.merchant_walk_time_min
  const distanceM = session.merchant_distance_m

  return (
    <button
      onClick={() => navigate('/')}
      className="w-full bg-white rounded-2xl border-2 border-green-200 p-4 text-left transition-transform active:scale-[0.98] shadow-sm"
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-semibold text-green-700">Claim Active</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-gray-100 rounded-full px-2.5 py-1">
            <Clock className="w-3.5 h-3.5 text-[#65676B]" />
            <span className="text-sm font-mono font-medium text-[#050505]">
              {minutes}:{seconds.toString().padStart(2, '0')}
            </span>
          </div>
          <ChevronRight className="w-4 h-4 text-gray-400" />
        </div>
      </div>

      {/* Walking path */}
      <div className="flex items-center gap-3 mb-3">
        <div className="flex flex-col items-center gap-0.5">
          <Zap className="w-4 h-4 text-green-600" />
          <div className="w-0.5 h-5 bg-green-200" />
          <MapPin className="w-4 h-4 text-[#1877F2]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-[#65676B] truncate">{chargerName}</p>
          <div className="flex items-center gap-1 my-1">
            <div className="flex-1 h-1 bg-green-100 rounded-full" />
            {distanceM != null && (
              <span className="text-xs text-[#65676B]">{distanceM < 1000 ? `${Math.round(distanceM)}m` : `${(distanceM / 1609.34).toFixed(1)}mi`}</span>
            )}
            {walkMin != null && !distanceM && (
              <span className="text-xs text-[#65676B]">{walkMin}min</span>
            )}
          </div>
          <p className="text-xs font-medium text-[#050505] truncate">{merchantName}</p>
        </div>
      </div>

      {/* Offer */}
      {offerTitle && (
        <div className="flex items-center gap-2 bg-green-50 rounded-xl px-3 py-2">
          <Gift className="w-4 h-4 text-green-600 flex-shrink-0" />
          <span className="text-sm font-medium text-green-700 truncate">{offerTitle}</span>
        </div>
      )}

      {/* Expiry context */}
      {session.charging_active && (
        <p className="text-xs text-[#65676B] mt-2 text-center">
          Expires 1 hour after your charge ends
        </p>
      )}
    </button>
  )
}
