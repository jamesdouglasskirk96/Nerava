import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Clock, MapPin, Zap, Navigation, Gift, CheckCircle, Loader2 } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { useActiveExclusive, useCompleteExclusive } from '../../services/api'
import type { ExclusiveSessionResponse } from '../../services/api'
import { openExternalUrl } from '../../utils/openExternal'

function formatCountdown(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function ClaimDetailsScreen() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { data: activeData, isLoading } = useActiveExclusive()
  const completeExclusive = useCompleteExclusive()
  const [remainingSeconds, setRemainingSeconds] = useState(0)
  const [completing, setCompleting] = useState(false)
  const [completed, setCompleted] = useState(false)

  const session: ExclusiveSessionResponse | null = activeData?.exclusive_session ?? null

  // Countdown timer
  useEffect(() => {
    if (!session) return
    const update = () => {
      const expiresAt = new Date(session.expires_at).getTime()
      const now = Date.now()
      setRemainingSeconds(Math.max(0, Math.floor((expiresAt - now) / 1000)))
    }
    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [session])

  const handleComplete = async () => {
    if (!session) return
    setCompleting(true)
    try {
      await completeExclusive.mutateAsync({ exclusive_session_id: session.id })
      setCompleted(true)
      setTimeout(() => navigate('/'), 2500)
    } catch {
      setCompleting(false)
    }
  }

  const handleDirections = () => {
    if (session?.merchant_lat && session?.merchant_lng) {
      openExternalUrl(
        `https://www.google.com/maps/dir/?api=1&destination=${session.merchant_lat},${session.merchant_lng}`
      )
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-white">
        <Loader2 className="w-8 h-8 animate-spin text-green-600" />
      </div>
    )
  }

  if (!session || (sessionId && session.id !== sessionId)) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-white px-6 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <Clock className="w-8 h-8 text-gray-400" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Claim Expired</h2>
        <p className="text-sm text-gray-500 mb-6">This claim is no longer active.</p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-3 bg-[#1877F2] text-white font-semibold rounded-xl"
        >
          Back to Home
        </button>
      </div>
    )
  }

  if (completed) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-white px-6 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Visit Complete</h2>
        <p className="text-sm text-gray-500">
          Your visit to {session.merchant_name || 'the merchant'} has been recorded.
        </p>
      </div>
    )
  }

  const isExpired = remainingSeconds <= 0
  const isUrgent = remainingSeconds > 0 && remainingSeconds <= 300

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-gray-100">
        <button onClick={() => navigate(-1)} className="p-1">
          <ArrowLeft className="w-5 h-5 text-gray-700" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-sm font-semibold text-green-700">Claim Active</span>
          </div>
        </div>
        <div className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 ${
          isExpired ? 'bg-red-100' : isUrgent ? 'bg-orange-100' : 'bg-gray-100'
        }`}>
          <Clock className={`w-4 h-4 ${isExpired ? 'text-red-600' : isUrgent ? 'text-orange-600' : 'text-[#65676B]'}`} />
          <span className={`text-sm font-mono font-semibold ${
            isExpired ? 'text-red-700' : isUrgent ? 'text-orange-700' : 'text-[#050505]'
          }`}>
            {formatCountdown(remainingSeconds)}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-5">
        {/* Merchant info */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[#050505] mb-1">
            {session.merchant_name || 'Merchant'}
          </h1>
          {session.merchant_category && (
            <p className="text-sm text-[#65676B] capitalize">{session.merchant_category.replace(/_/g, ' ')}</p>
          )}
        </div>

        {/* Offer */}
        {session.exclusive_title && (
          <div className="bg-green-50 border border-green-200 rounded-2xl p-4 flex items-start gap-3">
            <Gift className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-semibold text-green-800">{session.exclusive_title}</p>
              <p className="text-sm text-green-700 mt-0.5">Show this screen at the counter</p>
            </div>
          </div>
        )}

        {/* QR Code */}
        {session.verification_code && (
          <div className="bg-gray-50 rounded-2xl p-6 flex flex-col items-center">
            <QRCodeSVG
              value={session.verification_code}
              size={180}
              level="M"
              includeMargin={false}
            />
            <p className="mt-3 text-lg font-mono font-bold tracking-wider text-[#050505]">
              {session.verification_code}
            </p>
            <p className="text-xs text-[#65676B] mt-1">Merchant scans to verify your visit</p>
          </div>
        )}

        {/* Distance info */}
        <div className="bg-gray-50 rounded-2xl p-4">
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-center gap-0.5">
              <Zap className="w-4 h-4 text-green-600" />
              <div className="w-0.5 h-6 bg-green-200" />
              <MapPin className="w-4 h-4 text-[#1877F2]" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-[#65676B]">{session.charger_name || 'Your Charger'}</p>
              <div className="flex items-center gap-2 my-1.5">
                {session.merchant_distance_m != null && (
                  <span className="text-sm font-medium text-[#050505]">
                    {session.merchant_distance_m < 1000
                      ? `${Math.round(session.merchant_distance_m)}m`
                      : `${(session.merchant_distance_m / 1609.34).toFixed(1)} miles`}
                  </span>
                )}
                {session.merchant_walk_time_min != null && (
                  <span className="text-sm text-[#65676B]">
                    · {session.merchant_walk_time_min} min walk
                  </span>
                )}
              </div>
              <p className="text-xs font-medium text-[#050505]">
                {session.merchant_name || 'Merchant'}
              </p>
            </div>
          </div>
        </div>

        {/* Charging status */}
        {session.charging_active != null && (
          <div className={`rounded-2xl p-3 flex items-center gap-2 ${
            session.charging_active ? 'bg-green-50 border border-green-200' : 'bg-gray-50'
          }`}>
            <Zap className={`w-4 h-4 ${session.charging_active ? 'text-green-600' : 'text-gray-400'}`} />
            <p className={`text-sm ${session.charging_active ? 'text-green-700' : 'text-[#65676B]'}`}>
              {session.charging_active
                ? 'Charging active — claim expires 1hr after charge ends'
                : `Charge ended — ${formatCountdown(remainingSeconds)} remaining`}
            </p>
          </div>
        )}
      </div>

      {/* Bottom actions */}
      <div className="p-4 pb-8 space-y-3 border-t border-gray-100" style={{ paddingBottom: 'max(2rem, env(safe-area-inset-bottom))' }}>
        {session.merchant_lat && session.merchant_lng && (
          <button
            onClick={handleDirections}
            className="w-full py-3.5 text-sm font-semibold text-[#1877F2] border-2 border-[#1877F2] rounded-xl flex items-center justify-center gap-2 active:scale-[0.98] transition-transform"
          >
            <Navigation className="w-4 h-4" />
            Get Directions
          </button>
        )}
        <button
          onClick={handleComplete}
          disabled={completing || isExpired}
          className="w-full py-3.5 text-sm font-semibold text-white bg-green-600 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50 active:scale-[0.98] transition-transform"
        >
          {completing ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Verifying...</>
          ) : (
            <><CheckCircle className="w-4 h-4" /> I'm at the Merchant — Done</>
          )}
        </button>
      </div>
    </div>
  )
}
