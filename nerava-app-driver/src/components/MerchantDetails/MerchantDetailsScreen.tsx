import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { Navigation, X, Heart, Share2 } from 'lucide-react'
import { useMerchantDetails, useWalletActivate, useShareLink } from '../../services/api'
import { HeroImageHeader } from './HeroImageHeader'
import { DistanceCard } from './DistanceCard'
import { HoursCard } from './HoursCard'
import { ExclusiveOfferCard } from './ExclusiveOfferCard'
import { LocationStatusCard } from './LocationStatusCard'
import { WalletSuccessModal } from '../WalletSuccess/WalletSuccessModal'
import { PreferencesModal } from '../Preferences/PreferencesModal'
import { Button } from '../shared/Button'
import { ActivateExclusiveModal } from '../ActivateExclusiveModal/ActivateExclusiveModal'
import { useFavoriteMerchant } from '../../hooks/useFavoriteMerchant'
import { useGeolocation, CHARGER_RADIUS_M } from '../../hooks/useGeolocation'

export function MerchantDetailsScreen() {
  const { merchantId } = useParams<{ merchantId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('session_id') || undefined
  const chargerId = searchParams.get('charger_id') || undefined

  const { data: merchantData, isLoading, error } = useMerchantDetails(merchantId || null, sessionId)
  const walletActivate = useWalletActivate()
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [showPreferencesModal, setShowPreferencesModal] = useState(false)
  const [showExclusiveModal, setShowExclusiveModal] = useState(false)
  const [walletState, setWalletState] = useState<{ activeCopy?: string } | null>(null)

  // Favorites hook
  const { isFavorite, toggleFavorite } = useFavoriteMerchant(merchantId || null)

  // Share link
  const { data: shareData } = useShareLink(merchantId || null)

  // Geolocation for proximity-based activation
  const geo = useGeolocation(5000) // Poll every 5 seconds

  // Check if preferences modal should be shown (only once per session)
  useEffect(() => {
    const hasSeenPreferences = sessionStorage.getItem('preferences_modal_shown')
    if (showSuccessModal && !hasSeenPreferences) {
      // Will show preferences modal after success modal closes
    }
  }, [showSuccessModal])

  const handleAddToWallet = async () => {
    // If we have session_id, use wallet activation flow
    if (sessionId && merchantId) {
      try {
        const response = await walletActivate.mutateAsync({
          session_id: sessionId,
          merchant_id: merchantId,
        })
        setWalletState(response.wallet_state)
        setShowSuccessModal(true)
      } catch (err) {
        alert('Failed to activate exclusive: ' + (err instanceof Error ? err.message : 'Unknown error'))
      }
      return
    }

    // Otherwise, use exclusive activation flow (OTP modal)
    if (merchantId && chargerId) {
      setShowExclusiveModal(true)
      return
    }

    alert('Missing merchant ID or charger ID')
  }

  const handleExclusiveSuccess = () => {
    setShowExclusiveModal(false)
    // Navigate to the Exclusive Active screen after OTP verification
    navigate(`/app/exclusive/${merchantId}`)
  }

  const handleShare = async () => {
    if (!shareData) return

    // Use Web Share API if available
    if (navigator.share) {
      try {
        await navigator.share({
          title: shareData.title,
          text: shareData.description,
          url: shareData.url,
        })
      } catch (err) {
        // User cancelled or error
        console.log('Share cancelled or failed:', err)
      }
    } else {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(shareData.url)
        alert('Link copied to clipboard!')
      } catch (err) {
        console.error('Failed to copy:', err)
      }
    }
  }

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false)
    // Show preferences modal only once per session
    const hasSeenPreferences = sessionStorage.getItem('preferences_modal_shown')
    if (!hasSeenPreferences) {
      setShowPreferencesModal(true)
      sessionStorage.setItem('preferences_modal_shown', 'true')
    }
  }

  const handleGetDirections = () => {
    if (merchantData?.actions.get_directions_url) {
      window.open(merchantData.actions.get_directions_url, '_blank')
    } else {
      // Fallback - should not happen if API provides get_directions_url
      console.warn('No directions URL available')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">Loading merchant details...</p>
      </div>
    )
  }

  if (error || !merchantData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="text-center">
          <p className="text-gray-900 font-medium mb-2">Merchant not found</p>
          <p className="text-gray-600 text-sm">{error?.message || 'Unknown error'}</p>
        </div>
      </div>
    )
  }

  // Extract data for components
  // Check if photo_urls array exists (may not be typed)
  const photoUrls = (merchantData.merchant as any).photo_urls
  const walkTime = merchantData.moment.label // e.g., "3 min walk"
  const isExclusive = merchantData.perk?.badge === 'Exclusive'
  
  // Extract hours data if available (may not be in typed response)
  const merchantAny = merchantData.merchant as any
  const hoursToday = merchantAny.hours_today || merchantAny.hours || undefined
  const openNow = merchantAny.open_now !== undefined ? merchantAny.open_now : undefined
  const hoursText = merchantAny.hours_text || undefined

  const handleCTA = () => {
    if (geo.isNearCharger) {
      handleAddToWallet()
    } else {
      // Open Google Maps directions to charger location
      const chargerLat = 30.4027
      const chargerLng = -97.6719
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${chargerLat},${chargerLng}`, '_blank')
    }
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-white overflow-hidden">
      {/* Sticky Header Bar - ALWAYS visible */}
      <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 bg-white/95 backdrop-blur-sm border-b border-gray-100">
        <button onClick={() => navigate(-1)} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
          <X className="w-5 h-5" />
        </button>
        <div className="flex gap-2">
          <button onClick={toggleFavorite} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
            <Heart className={`w-5 h-5 ${isFavorite ? 'fill-red-500 text-red-500' : ''}`} />
          </button>
          <button onClick={handleShare} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Single Scrollable Content Area */}
      <div className="flex-1 overflow-y-auto">
        {/* Hero Image - max 35-40% of viewport */}
        <HeroImageHeader
          photoUrls={photoUrls}
          photoUrl={merchantData.merchant.photo_url}
          merchantName={merchantData.merchant.name}
          category={merchantData.merchant.category}
          walkTime={walkTime}
          isExclusive={isExclusive}
          onClose={() => navigate(-1)}
          onFavorite={toggleFavorite}
          onShare={handleShare}
          isFavorite={isFavorite}
        />

        {/* Content */}
        <div className="px-5 py-4 space-y-4">
          {/* Merchant name + category */}
          <div>
            <h1 className="text-2xl font-bold text-[#050505]">{merchantData.merchant.name}</h1>
            {merchantData.merchant.category && (
              <p className="text-sm text-[#65676B]">{merchantData.merchant.category}</p>
            )}
          </div>

          {/* Exclusive Offer Card - HIGH PRIORITY, visible without scrolling */}
          {merchantData.perk && (
            <ExclusiveOfferCard
              title={merchantData.perk.title}
              description={merchantData.perk.description}
            />
          )}

          {/* Distance Card */}
          {(merchantData.moment.distance_miles ?? 0) > 0 && (
            <DistanceCard
              distanceMiles={merchantData.moment.distance_miles}
            />
          )}

          {/* Hours card - only show if hours data exists */}
          {(hoursText || hoursToday) && (
            <HoursCard
              hoursText={hoursText}
              hoursToday={hoursToday}
              openNow={openNow}
            />
          )}

          {/* Merchant description */}
          {merchantAny.description && (
            <p className="text-sm text-[#65676B] leading-relaxed">
              {merchantAny.description}
            </p>
          )}

          {/* Location Status - CALM design, not red error */}
          <LocationStatusCard geo={geo} />
        </div>
      </div>

      {/* Sticky Bottom CTA */}
      <div className="sticky bottom-0 px-5 py-4 bg-white border-t border-gray-100 safe-area-inset-bottom">
        {geo.isNearCharger ? (
          merchantData.wallet.can_add ? (
            <Button
              variant="primary"
              onClick={handleCTA}
              disabled={walletActivate.isPending}
              className="w-full"
            >
              {walletActivate.isPending ? 'Activating...' : 'Activate Exclusive'}
            </Button>
          ) : (
            <Button
              variant="secondary"
              onClick={handleGetDirections}
              className="w-full"
            >
              Get Directions
            </Button>
          )
        ) : (
          <>
            <Button
              variant="secondary"
              onClick={() => {
                const chargerLat = 30.4027
                const chargerLng = -97.6719
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${chargerLat},${chargerLng}`, '_blank')
              }}
              className="w-full flex items-center justify-center gap-2"
            >
              <Navigation className="w-4 h-4" />
              Navigate to Charger
            </Button>
            {merchantData.wallet.can_add && (
              <Button
                variant="primary"
                disabled={true}
                className="w-full opacity-50 mt-2"
              >
                Activate after arrival
              </Button>
            )}
          </>
        )}
      </div>

      {/* Success modal */}
      {showSuccessModal && merchantData && (
        <WalletSuccessModal
          merchantName={merchantData.merchant.name}
          perkTitle={merchantData.perk.title}
          activeCopy={walletState?.activeCopy}
          onClose={handleSuccessModalClose}
        />
      )}

      {/* Preferences modal */}
      <PreferencesModal
        isOpen={showPreferencesModal}
        onClose={() => setShowPreferencesModal(false)}
      />

      {/* Exclusive activation modal (OTP flow) */}
      <ActivateExclusiveModal
        isOpen={showExclusiveModal}
        onClose={() => setShowExclusiveModal(false)}
        onSuccess={handleExclusiveSuccess}
        merchantId={merchantId}
        chargerId={chargerId}
      />
    </div>
  )
}

