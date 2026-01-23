// Merchant Detail Modal - Full-screen modal with merchant details
import { ArrowLeft, MapPin, Clock, Wallet, Heart, Share2 } from 'lucide-react'
import { ImageWithFallback } from '../shared/ImageWithFallback'
import type { MockMerchant } from '../../mock/mockMerchants'

interface MerchantDetailModalProps {
  merchant: MockMerchant
  isCharging: boolean
  isInChargerRadius: boolean
  onClose: () => void
  onToggleLike: (merchantId: string) => void
  onActivateExclusive: (merchant: MockMerchant) => void
  likedMerchants: Set<string>
}

/**
 * Full-screen modal with merchant image, distance, hours, description
 * CTA logic:
 * - PRE_CHARGING → "Activate after arrival" (disabled)
 * - CHARGING_ACTIVE → "Activate Exclusive" (enabled)
 */
export function MerchantDetailModal({
  merchant,
  isCharging,
  isInChargerRadius,
  onClose,
  onToggleLike,
  onActivateExclusive,
  likedMerchants,
}: MerchantDetailModalProps) {
  const isLiked = likedMerchants.has(merchant.id)
  const hasExclusive = merchant.badges?.includes('Exclusive') || false

  // Dynamic font size for titles to ensure single line
  const getTitleFontSize = (name: string) => {
    const length = name.length
    if (length <= 20) return '1.875rem' // text-3xl
    if (length <= 25) return '1.75rem' // text-[1.75rem]
    if (length <= 30) return '1.5rem' // text-2xl
    if (length <= 35) return '1.25rem' // text-xl
    return '1.125rem' // text-lg
  }

  const handleShare = () => {
    const url = `https://nerava.com/merchant/${merchant.id}`
    navigator.clipboard.writeText(url)
  }

  return (
    <div className="fixed inset-0 bg-[#242526] z-50">
      <div className="h-screen max-w-md mx-auto bg-white flex flex-col overflow-hidden">
        {/* Hero Image */}
        <div className="relative h-56 flex-shrink-0">
          <ImageWithFallback
            src={merchant.imageUrl}
            alt={merchant.name}
            category={merchant.category || 'coffee'}
            className="w-full h-full"
          />

          {/* Back Button */}
          <button
            onClick={onClose}
            className="absolute top-4 left-4 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-[#050505]" />
          </button>

          {/* Action Buttons - Heart and Share */}
          <div className="absolute top-4 right-4 flex gap-2">
            <button
              onClick={() => onToggleLike(merchant.id)}
              className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all ${
                isLiked ? 'bg-[#1877F2] text-white' : 'bg-white text-[#050505]'
              }`}
            >
              <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
            </button>
            <button
              onClick={handleShare}
              className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
            >
              <Share2 className="w-5 h-5 text-[#050505]" />
            </button>
          </div>

          {/* Walk Time Badge */}
          <div className="absolute bottom-4 left-4">
            <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
              <span className="text-sm text-white font-medium">{merchant.walkTime}</span>
            </div>
          </div>

          {/* Exclusive Badge - positioned under favorite button */}
          {hasExclusive && (
            <div className="absolute bottom-4 right-4">
              <div className="px-3 py-1.5 bg-white rounded-full border border-yellow-500/30 shadow-lg">
                <span className="text-sm text-yellow-700 font-medium">⭐ Exclusive</span>
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 px-6 py-5 overflow-hidden flex flex-col">
          {/* Title */}
          <div className="mb-1 flex-shrink-0">
            <h1
              className="text-3xl inline whitespace-nowrap overflow-hidden text-ellipsis max-w-full"
              style={{ fontSize: getTitleFontSize(merchant.name) }}
            >
              {merchant.name}
            </h1>
          </div>

          {/* Category */}
          {merchant.category && (
            <p className="text-sm text-[#65676B] mb-3 flex-shrink-0">{merchant.category}</p>
          )}

          {/* Exclusive Offer - Show prominently if it exists */}
          {hasExclusive && merchant.exclusiveOffer && (
            <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-2xl p-4 mb-4 flex-shrink-0 border border-yellow-600/20">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Wallet className="w-4 h-4 text-yellow-700" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-sm mb-0.5 text-yellow-900">Exclusive Offer</h3>
                  <p className="text-sm text-yellow-800">
                    {merchant.exclusiveOffer}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Distance Info */}
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-3 flex-shrink-0">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-[#1877F2]" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5">Distance</h3>
                <p className="text-xs text-[#65676B]">
                  {merchant.distance || '0.2 miles'} · Fits your charge window
                </p>
              </div>
            </div>
          </div>

          {/* Hours */}
          {merchant.hours && (
            <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-4 flex-shrink-0">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                  <Clock className="w-4 h-4 text-[#1877F2]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-sm mb-0.5">Hours Today</h3>
                  <p className="text-xs text-[#65676B]">
                    {merchant.hours} · {merchant.hoursStatus || 'Open now'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Description - Only show for merchants in charging state */}
          {isCharging && merchant.description && (
            <div className="mb-5 flex-shrink-0">
              <div className="text-sm text-[#65676B] leading-relaxed max-h-32 overflow-y-auto pr-2">
                <p className="whitespace-pre-line">{merchant.description}</p>
              </div>
            </div>
          )}

          {/* CTA Buttons */}
          <div className="flex flex-col gap-3 flex-shrink-0 mt-auto">
            <button
              onClick={() => {
                // Open Google Maps with directions
                const merchantAddress = encodeURIComponent(merchant.name)
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${merchantAddress}`, '_blank')
              }}
              className="w-full py-3.5 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all"
            >
              {isCharging ? 'Get Directions' : 'Navigate to Charger'}
            </button>
            {hasExclusive && (
              <div className="relative">
                <button
                  onClick={() => isCharging && isInChargerRadius && onActivateExclusive(merchant)}
                  disabled={!isCharging || !isInChargerRadius}
                  className={`w-full py-3.5 rounded-2xl font-medium transition-all flex items-center justify-center gap-2 ${
                    isCharging && isInChargerRadius
                      ? 'bg-[#1877F2] text-white hover:bg-[#166FE5] active:scale-98'
                      : 'bg-[#E4E6EB] text-[#65676B] cursor-not-allowed'
                  }`}
                >
                  <Wallet className="w-5 h-5" />
                  {!isCharging ? 'Activate after arrival' : 'Activate Exclusive'}
                </button>
                {!isCharging && (
                  <p className="text-xs text-[#65676B] text-center mt-2">
                    Available once you arrive and start charging
                  </p>
                )}
                {isCharging && !isInChargerRadius && (
                  <p className="text-xs text-[#65676B] text-center mt-2">
                    Available once you start charging
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

