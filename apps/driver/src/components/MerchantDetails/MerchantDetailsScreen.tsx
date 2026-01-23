import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useMerchantDetails, useWalletActivate, useActivateExclusive, useCompleteExclusive } from '../../services/api'
import { HeroImageHeader } from './HeroImageHeader'
import { DistanceCard } from './DistanceCard'
import { HoursCard } from './HoursCard'
import { ExclusiveOfferCard } from './ExclusiveOfferCard'
import { WalletSuccessModal } from '../WalletSuccess/WalletSuccessModal'
import { PreferencesModal } from '../Preferences/PreferencesModal'
import { ActivateExclusiveCodeModal } from '../ActivateExclusiveCodeModal/ActivateExclusiveCodeModal'
import { Button } from '../shared/Button'

export function MerchantDetailsScreen() {
  const { merchantId } = useParams<{ merchantId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('session_id') || undefined
  const chargerId = searchParams.get('charger_id') || 'canyon_ridge_tesla' // Default to Canyon Ridge

  const { data: merchantData, isLoading, error } = useMerchantDetails(merchantId || null, sessionId)
  const walletActivate = useWalletActivate()
  const activateExclusive = useActivateExclusive()
  const completeExclusive = useCompleteExclusive()
  
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [showPreferencesModal, setShowPreferencesModal] = useState(false)
  const [showMoreAbout, setShowMoreAbout] = useState(false)
  const [showActivateModal, setShowActivateModal] = useState(false)
  const [walletActiveCopy, setWalletActiveCopy] = useState<string | null>(null)
  const [exclusiveActive, setExclusiveActive] = useState(false)
  const [exclusiveSessionId, setExclusiveSessionId] = useState<string | null>(null)

  // Check if preferences modal should be shown (only once per session)
  useEffect(() => {
    const hasSeenPreferences = sessionStorage.getItem('preferences_modal_shown')
    if (showSuccessModal && !hasSeenPreferences) {
      // Will show preferences modal after success modal closes
    }
  }, [showSuccessModal])

  const handleActivateExclusive = async (code: string) => {
    if (!merchantId) {
      alert('Missing merchant ID')
      return
    }

    try {
      // Get current location
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject)
      })

      const response = await activateExclusive.mutateAsync({
        merchant_id: merchantId,
        merchant_place_id: merchantId, // Use merchantId as place_id
        charger_id: chargerId,
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy_m: position.coords.accuracy || undefined,
      })

      setExclusiveActive(true)
      setExclusiveSessionId(response.exclusive_session.id)
      setShowActivateModal(false)
      setShowSuccessModal(true)
    } catch (err) {
      throw err // Re-throw to let modal handle error display
    }
  }

  const handleCompleteExclusive = async () => {
    if (!exclusiveSessionId) {
      alert('No active exclusive session')
      return
    }

    try {
      await completeExclusive.mutateAsync({
        exclusive_session_id: exclusiveSessionId,
      })
      
      // Navigate back or show completion success
      navigate('/wyc')
    } catch (err) {
      alert('Failed to complete exclusive: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  const handleAddToWallet = async () => {
    // Show activation modal instead of wallet activation
    setShowActivateModal(true)
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
  const isExclusive = merchantData.perk.badge === 'Exclusive'

  return (
    <div className="min-h-screen bg-white">
      {/* Hero image */}
      <HeroImageHeader
        photoUrls={photoUrls}
        photoUrl={merchantData.merchant.photo_url}
        merchantName={merchantData.merchant.name}
        category={merchantData.merchant.category}
        walkTime={walkTime}
        isExclusive={isExclusive}
        onClose={() => navigate(-1)}
        onFavorite={() => {
          // TODO: Implement favorite functionality
        }}
        onShare={() => {
          // TODO: Implement share functionality
        }}
      />

      {/* Content */}
      <div className="px-4 py-6 space-y-5">
        {/* Merchant name and category - NO badge */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 leading-tight mb-2">{merchantData.merchant.name}</h1>
          <p className="text-base text-gray-600">{merchantData.merchant.category}</p>
        </div>

        {/* Exclusive Offer Card */}
        <ExclusiveOfferCard
          title={merchantData.perk.title}
          description={merchantData.perk.description}
        />

        {/* Distance card */}
        <DistanceCard
          distanceMiles={merchantData.moment.distance_miles}
        />

        {/* Hours card */}
        {/* Note: Hours data not currently in MerchantDetailsResponse type */}
        <HoursCard />

        {/* Description paragraph */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-700 leading-relaxed">
            {merchantData.perk.description}
          </p>
        </div>

        {/* Get Directions button - secondary variant */}
        <Button
          variant="secondary"
          className="w-full"
          onClick={handleGetDirections}
        >
          Get Directions
        </Button>

        {/* Activate Exclusive button - primary variant */}
        {!exclusiveActive && merchantData.wallet.can_add && (
          <Button
            variant="primary"
            className="w-full"
            onClick={handleAddToWallet}
            disabled={activateExclusive.isPending}
          >
            {activateExclusive.isPending ? 'Activating...' : 'Activate Exclusive'}
          </Button>
        )}

        {/* Done button when exclusive is active */}
        {exclusiveActive && (
          <Button
            variant="primary"
            className="w-full"
            onClick={handleCompleteExclusive}
            disabled={completeExclusive.isPending}
          >
            {completeExclusive.isPending ? 'Completing...' : "I'm at the Merchant - Done"}
          </Button>
        )}
      </div>

      {/* Success modal */}
      {showSuccessModal && merchantData && (
        <WalletSuccessModal
          merchantName={merchantData.merchant.name}
          perkTitle={merchantData.perk.title}
          activeCopy={walletActiveCopy ?? undefined}
          onClose={handleSuccessModalClose}
        />
      )}

      {/* Preferences modal */}
      <PreferencesModal
        isOpen={showPreferencesModal}
        onClose={() => setShowPreferencesModal(false)}
      />

      {/* Activate Exclusive Code Modal */}
      <ActivateExclusiveCodeModal
        isOpen={showActivateModal}
        onClose={() => setShowActivateModal(false)}
        onActivate={handleActivateExclusive}
        merchantName={merchantData?.merchant.name}
        exclusiveTitle={merchantData?.perk.title}
      />
    </div>
  )
}

