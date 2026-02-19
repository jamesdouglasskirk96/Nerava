// Exclusive Active View - Replaces discovery view when exclusive is active
import { MapPin, Clock, Heart, Share2, Navigation, QrCode, AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ImageWithFallback } from '../shared/ImageWithFallback'
import { FullScreenTicket } from '../shared/FullScreenTicket'
import { FEATURE_FLAGS } from '../../config/featureFlags'
import { capture, DRIVER_EVENTS } from '../../analytics'
import type { ExclusiveMerchant } from '../../hooks/useExclusiveSessionState'
import type { RefuelDetails } from '../RefuelIntentModal'

interface ExclusiveActiveViewProps {
  merchant: ExclusiveMerchant
  remainingMinutes: number
  onArrived: () => void
  onCancel?: () => void
  onExpired?: () => void
  onToggleLike?: (merchantId: string) => void
  onShare?: () => void
  isLiked?: boolean
  reservationId?: string
  refuelDetails?: RefuelDetails | null
}

/**
 * Exclusive Active View - Replaces entire discovery view when exclusive is active
 * Shows:
 * - Sticky banner: "Exclusive Active"
 * - Countdown timer (60 min, updates every minute)
 * - Instruction: "Walk to {merchant.name} and show this screen"
 * - Distance + walking instructions
 * - CTA: "I'm at the Merchant"
 * All other merchants hidden
 */
export function ExclusiveActiveView({
  merchant,
  remainingMinutes,
  onArrived,
  onCancel,
  onExpired,
  onToggleLike,
  onShare,
  isLiked = false,
  reservationId,
  refuelDetails,
}: ExclusiveActiveViewProps) {
  const navigate = useNavigate()
  const minutes = remainingMinutes
  const isExpired = minutes <= 0
  const [showFullscreenTicket, setShowFullscreenTicket] = useState(false)

  return (
    <div className="fixed inset-0 bg-white z-50">
      <div className="h-[100vh] h-[100dvh] max-h-[100dvh] max-w-md mx-auto bg-white flex flex-col overflow-hidden">
        {/* Hero Image */}
        <div className="relative h-64 flex-shrink-0">
          <ImageWithFallback
            src={merchant.imageUrl}
            alt={merchant.name}
            category={merchant.category || 'coffee'}
            className="w-full h-full"
          />
          
          {/* Status Bar */}
          <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="w-9 h-9 bg-black/30 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-black/50 active:scale-95 transition-all"
                  aria-label="Close session"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              )}
              <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
                <span className="text-xs text-white font-medium">
                  {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 ? 'Active Session' : 'Exclusive Active'}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              {onToggleLike && (
                <button
                  onClick={() => onToggleLike(merchant.id)}
                  className={`w-11 h-11 rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all ${
                    isLiked
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-white text-[#050505]'
                  }`}
                  aria-label={isLiked ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
                </button>
              )}
              {onShare && (
                <button
                  onClick={onShare}
                  className="w-11 h-11 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
                  aria-label="Share merchant"
                >
                  <Share2 className="w-5 h-5 text-[#050505]" />
                </button>
              )}
            </div>
          </div>

          {/* Countdown Timer — color-coded urgency */}
          <div className="absolute bottom-4 left-4 right-4 flex justify-center">
            <div
              className={`px-4 py-2 backdrop-blur-sm rounded-full border ${
                minutes <= 0
                  ? 'bg-red-50/95 border-red-300'
                  : minutes <= 5
                  ? 'bg-red-50/95 border-red-300'
                  : minutes <= 15
                  ? 'bg-yellow-50/95 border-yellow-300'
                  : 'bg-white/95 border-[#E4E6EB]'
              }`}
              role="timer"
              aria-live="polite"
              aria-atomic="true"
              aria-label={
                minutes <= 0
                  ? 'Session expired'
                  : `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} remaining`
              }
            >
              <span className={`text-sm font-medium ${
                minutes <= 0
                  ? 'text-red-600'
                  : minutes <= 5
                  ? 'text-red-600'
                  : minutes <= 15
                  ? 'text-yellow-700'
                  : 'text-[#050505]'
              }`}>
                {minutes <= 0
                  ? 'Expired'
                  : `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} remaining`
                }
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 px-6 py-6 overflow-y-auto flex flex-col">
          {/* Title */}
          <h1 className="text-3xl mb-1">{merchant.name}</h1>

          {/* Category */}
          {merchant.category && (
            <p className="text-sm text-[#65676B] mb-6">{merchant.category}</p>
          )}

          {/* Instruction */}
          <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-4">
            <p className="text-sm text-[#050505] text-center">
              Walk to <span className="font-medium">{merchant.name}</span> and show this screen
            </p>
          </div>

          {/* Distance Info */}
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-3">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-[#1877F2]" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5">Distance</h3>
                <p className="text-xs text-[#65676B]">
                  {merchant.distance || "0.2 miles"} · {merchant.walkTime}
                </p>
              </div>
            </div>
          </div>

          {/* Hours */}
          {merchant.hours && (
            <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-6">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                  <Clock className="w-4 h-4 text-[#1877F2]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-sm mb-0.5">Hours Today</h3>
                  <p className="text-xs text-[#65676B]">
                    {merchant.hours} · {merchant.hoursStatus || "Open now"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* CTA Buttons */}
          <div className="mt-auto space-y-3">
            {/* Show Host Button - Signature interaction */}
            {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 && reservationId && (
              <button
                onClick={() => {
                  setShowFullscreenTicket(true)
                  capture(DRIVER_EVENTS.SHOW_HOST_CLICKED || 'show_host_clicked', {
                    merchant_id: merchant.id,
                    merchant_name: merchant.name,
                    path: window.location.pathname,
                  })
                }}
                className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-bold hover:bg-[#166FE5] active:scale-98 transition-all flex items-center justify-center gap-2 shadow-lg"
              >
                <QrCode className="w-5 h-5" />
                Show Host
              </button>
            )}
            <button
              onClick={() => {
                // Track Get Directions click
                capture(DRIVER_EVENTS.GET_DIRECTIONS_CLICKED, {
                  merchant_id: merchant.id,
                  merchant_name: merchant.name,
                  path: window.location.pathname,
                })
                
                // Open Google Maps with directions to merchant
                // In production, use actual merchant coordinates
                const merchantAddress = encodeURIComponent(merchant.name)
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${merchantAddress}`, '_blank')
              }}
              className="w-full py-4 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all flex items-center justify-center gap-2"
            >
              <Navigation className="w-5 h-5" />
              Get Directions
            </button>
            <button
              onClick={() => {
                // Track I'm at the Merchant click
                capture(DRIVER_EVENTS.IM_AT_MERCHANT_CLICKED, {
                  merchant_id: merchant.id,
                  merchant_name: merchant.name,
                  path: window.location.pathname,
                })
                onArrived()
              }}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              I'm at the Merchant - Done
            </button>
          </div>
        </div>
      </div>

      {/* Fullscreen Ticket Modal */}
      {showFullscreenTicket && reservationId && (
        <FullScreenTicket
          reservationId={reservationId}
          merchantName={merchant.name}
          refuelDetails={refuelDetails}
          onClose={() => setShowFullscreenTicket(false)}
        />
      )}

      {/* Expiration Modal — shown when timer reaches 0 */}
      {isExpired && (
        <div className="fixed inset-0 bg-black/50 z-[70] flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl text-center">
            <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-5">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-2xl font-bold text-[#050505] mb-2">Your spot has expired</h2>
            <p className="text-sm text-[#65676B] mb-6">
              The reservation time for {merchant.name} has ended. You can secure a new spot to try again.
            </p>
            <button
              onClick={() => {
                capture(DRIVER_EVENTS.EXCLUSIVE_DONE_CLICKED || 'exclusive_expired_new_spot', {
                  merchant_id: merchant.id,
                  merchant_name: merchant.name,
                  expired: true,
                })
                onExpired?.()
                // Navigate back to discovery screen
                navigate('/')
              }}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-[0.98] transition-all mb-3"
            >
              Find a New Spot
            </button>
            <button
              onClick={() => {
                onExpired?.()
                navigate('/')
              }}
              className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-[0.98] transition-all"
            >
              Back to Chargers
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

