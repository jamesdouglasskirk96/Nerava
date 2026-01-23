// Exclusive Active View - Replaces discovery view when exclusive is active
import { MapPin, Clock, Heart, Share2, Navigation } from 'lucide-react'
import { ImageWithFallback } from '../shared/ImageWithFallback'
import { ExclusiveOfferCard } from '../MerchantDetails/ExclusiveOfferCard'
import type { ExclusiveMerchant } from '../../hooks/useExclusiveSessionState'

interface ExclusiveActiveViewProps {
  merchant: ExclusiveMerchant
  remainingMinutes: number
  onArrived: () => void
  onToggleLike?: (merchantId: string) => void
  onShare?: () => void
  isLiked?: boolean
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
  onToggleLike,
  onShare,
  isLiked = false,
}: ExclusiveActiveViewProps) {
  const minutes = remainingMinutes

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
            <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
              <span className="text-xs text-white font-medium">Exclusive Active</span>
            </div>
            <div className="flex gap-2">
              {onToggleLike && (
                <button
                  onClick={() => onToggleLike(merchant.id)}
                  className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all ${
                    isLiked 
                      ? 'bg-[#1877F2] text-white' 
                      : 'bg-white text-[#050505]'
                  }`}
                >
                  <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
                </button>
              )}
              {onShare && (
                <button
                  onClick={onShare}
                  className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
                >
                  <Share2 className="w-5 h-5 text-[#050505]" />
                </button>
              )}
            </div>
          </div>

          {/* Countdown Timer */}
          <div className="absolute bottom-4 left-4 right-4 flex justify-center">
            <div className="px-4 py-2 bg-white/95 backdrop-blur-sm rounded-full border border-[#E4E6EB]">
              <span className="text-sm text-[#050505] font-medium">
                {minutes} {minutes === 1 ? 'minute' : 'minutes'} remaining
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

          {/* Exclusive Offer Card */}
          {merchant.exclusiveOffer && (
            <ExclusiveOfferCard
              title="Exclusive Offer"
              description={merchant.exclusiveOffer}
            />
          )}

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
            <button
              onClick={() => {
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
              onClick={onArrived}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              I'm at the Merchant
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

