import { useState, useEffect, useMemo } from 'react'
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
import { track, AnalyticsEvents } from '../../lib/analytics'
import { getChargerDiscovery, getChargerFromDiscovery } from '../../api/chargers'

export function MerchantDetailsScreen() {
  const { merchantId } = useParams<{ merchantId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('session_id') || undefined
  const chargerId = searchParams.get('charger_id') || undefined
  const chargerLatParam = searchParams.get('charger_lat')
  const chargerLngParam = searchParams.get('charger_lng')
  
  // Get user location for fetching charger details
  const geoForCharger = useGeolocation()
  
  // Fetch charger details if charger_id is provided and we have user location
  const [chargerData, setChargerData] = useState<{ lat: number; lng: number } | null>(null)
  
  useEffect(() => {
    if (chargerId && geoForCharger.latitude && geoForCharger.longitude) {
      // Try to get charger from discovery
      getChargerDiscovery(geoForCharger.latitude, geoForCharger.longitude)
        .then((discovery) => {
          const charger = getChargerFromDiscovery(chargerId, discovery)
          if (charger) {
            setChargerData({ lat: charger.lat, lng: charger.lng })
          }
        })
        .catch(() => {
          // Ignore errors, will use fallback
        })
    }
  }, [chargerId, geoForCharger.latitude, geoForCharger.longitude])
  
  // Use charger coordinates from params, fetched data, or fallback
  const chargerCoordinates = useMemo(() => {
    if (chargerLatParam && chargerLngParam) {
      return {
        lat: parseFloat(chargerLatParam),
        lng: parseFloat(chargerLngParam),
      }
    }
    if (chargerData) {
      return chargerData
    }
    // Fallback to hardcoded coordinates (Domain Austin)
    return { lat: 30.4027, lng: -97.6719 }
  }, [chargerLatParam, chargerLngParam, chargerData])

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
  const geoLocation = useGeolocation(5000) // Poll every 5 seconds

  // Track merchant details opened
  useEffect(() => {
    if (merchantId) {
      track(AnalyticsEvents.MERCHANT_DETAILS_OPENED, { merchant_id: merchantId })
    }
  }, [merchantId])

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

  // Helper function to get today's hours from opening_hours JSON
  function getHoursToday(openingHours: any): string | undefined {
    if (!openingHours?.weekday_text) return undefined

    // Get today's day (0=Sunday, 1=Monday, etc. in JS)
    const today = new Date().getDay()
    // Convert to weekday_text index (which starts with Monday=0)
    const weekdayIndex = today === 0 ? 6 : today - 1

    const weekdayText = openingHours.weekday_text
    if (weekdayIndex < weekdayText.length) {
      const fullText = weekdayText[weekdayIndex]
      // Parse "Monday: 11:00 AM – 10:00 PM" -> "11 AM–10 PM"
      if (fullText.includes(':')) {
        const hoursPart = fullText.split(':').slice(1).join(':').trim()
        // Simplify format
        return hoursPart
          .replace(/:00/g, '')
          .replace(/\s+/g, ' ')
          .replace(' – ', '–')
          .replace(' - ', '–')
      }
    }
    return undefined
  }

  const handleCTA = () => {
    if (geoLocation.isNearCharger) {
      handleAddToWallet()
    } else {
      // Open Google Maps directions to charger location
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${chargerCoordinates.lat},${chargerCoordinates.lng}`, '_blank')
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

        {/* Content - Tighter spacing */}
        <div className="px-5 py-3 space-y-3">
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
              options={(merchantData.perk as any).options}
            />
          )}

          {/* Distance Card - only show if we have valid distance */}
          {(merchantData.moment.distance_miles ?? 0) > 0 && (
            <DistanceCard
              distanceMiles={merchantData.moment.distance_miles}
            />
          )}

          {/* Hours Today - show if available */}
          {(hoursToday || merchantAny.opening_hours) && (
            <HoursCard
              hoursToday={hoursToday || getHoursToday(merchantAny.opening_hours)}
              openNow={openNow}
            />
          )}

          {/* Description */}
          {merchantAny.description && (
            <p className="text-sm text-[#65676B] leading-relaxed">
              {merchantAny.description}
            </p>
          )}

          {/* Location Status - Only show if there's an error or warning */}
          {(geoLocation.error || geoLocation.distanceToCharger === null) && (
            <LocationStatusCard geo={geoLocation} />
          )}
        </div>
      </div>

      {/* Sticky Bottom CTA */}
      <div className="sticky bottom-0 px-5 py-4 bg-white border-t border-gray-100 safe-area-inset-bottom">
        {geoLocation.isNearCharger ? (
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
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${chargerCoordinates.lat},${chargerCoordinates.lng}`, '_blank')
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

