import { useState, useEffect, useCallback } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { useMerchantDetails, useActivateExclusive, useVerifyVisit, useCompleteExclusive, useVoteAmenity, ApiError } from '../../services/api'
import { FEATURE_FLAGS } from '../../config/featureFlags'
import { RefuelIntentModal, type RefuelDetails } from '../RefuelIntentModal'
import { SpotSecuredModal } from '../SpotSecuredModal'
import { generateReservationId } from '../../utils/reservationId'
import { HeroImageHeader } from './HeroImageHeader'
import { DistanceCard } from './DistanceCard'
import { HoursCard } from './HoursCard'
import { ExclusiveOfferCard } from './ExclusiveOfferCard'
import { SocialProofBadge } from '../shared/SocialProofBadge'
import { AmenityVotes } from '../shared/AmenityVotes'
import { PreferencesModal } from '../Preferences/PreferencesModal'
import { ActivateExclusiveModal } from '../ActivateExclusiveModal/ActivateExclusiveModal'
import { ExclusiveActivatedModal } from '../ExclusiveActivated/ExclusiveActivatedModal'
import { VerificationCodeModal } from '../VerificationCode/VerificationCodeModal'
import { ExclusiveCompletedModal } from '../ExclusiveCompleted/ExclusiveCompletedModal'
import { Button } from '../shared/Button'
import { InlineError } from '../shared/InlineError'
import { MerchantDetailsSkeleton } from '../shared/Skeleton'
import { ThumbsUp, ThumbsDown } from 'lucide-react'

// Flow states
type FlowState =
  | 'idle'              // Initial state, no exclusive active
  | 'activated'         // Just activated, showing ExclusiveActivatedModal
  | 'walking'           // User started walking, showing active state view
  | 'at_merchant'       // User clicked "I'm at the Merchant", showing VerificationCodeModal
  | 'preferences'       // Showing preferences modal
  | 'completed'         // Showing completion modal

export function MerchantDetailsScreen() {
  const { merchantId } = useParams<{ merchantId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const sessionId = searchParams.get('session_id') || undefined
  const chargerId = searchParams.get('charger_id') || 'canyon_ridge_tesla'
  const photoFromNav = searchParams.get('photo') || undefined

  const { data: merchantData, isLoading, error } = useMerchantDetails(merchantId || null, sessionId)
  const activateExclusive = useActivateExclusive()
  const verifyVisit = useVerifyVisit()
  const completeExclusive = useCompleteExclusive()
  const voteAmenityMutation = useVoteAmenity()

  // V3: Validate merchant data has required fields
  useEffect(() => {
    if (merchantData && !merchantData.merchant.place_id) {
      console.warn('[V3] Merchant missing place_id, sending merchant_place_id=null')
    }
  }, [merchantData])

  // Flow state management
  const [flowState, setFlowState] = useState<FlowState>('idle')
  const [showActivateModal, setShowActivateModal] = useState(false)
  const [exclusiveSessionId, setExclusiveSessionId] = useState<string | null>(null)
  const [remainingSeconds, setRemainingSeconds] = useState(3600) // 60 minutes default
  const [verificationCode, setVerificationCode] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('access_token'))
  
  // V3: Intent capture state (only used when SECURE_A_SPOT_V3 is enabled)
  const [showRefuelIntentModal, setShowRefuelIntentModal] = useState(false)
  const [showSpotSecuredModal, setShowSpotSecuredModal] = useState(false)
  const [refuelDetails, setRefuelDetails] = useState<RefuelDetails | null>(null)
  const [reservationId, setReservationId] = useState<string | null>(null)
  const [showCompactIntentSummary, setShowCompactIntentSummary] = useState(false)
  const [inlineError, setInlineError] = useState<string | null>(null)

  // Amenity voting state
  const [userAmenityVotes, setUserAmenityVotes] = useState<{
    bathroom: 'up' | 'down' | null
    wifi: 'up' | 'down' | null
  }>({ bathroom: null, wifi: null })
  const [localAmenityCounts, setLocalAmenityCounts] = useState<{
    bathroom: { upvotes: number; downvotes: number }
    wifi: { upvotes: number; downvotes: number }
  } | null>(null)
  const [showAmenityVoteModal, setShowAmenityVoteModal] = useState(false)
  const [selectedAmenity, setSelectedAmenity] = useState<'bathroom' | 'wifi' | null>(null)

  // Check for previous intent in localStorage for progressive disclosure
  useEffect(() => {
    if (FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 && FEATURE_FLAGS.SECURE_A_SPOT_V3) {
      try {
        const stored = localStorage.getItem('nerava_last_intent')
        if (stored) {
          const previousIntent: RefuelDetails = JSON.parse(stored)
          setRefuelDetails(previousIntent)
          setShowCompactIntentSummary(true)
        }
      } catch {
        // Invalid JSON, ignore
      }
    }
  }, [])

  // Load amenity votes from localStorage and initialize counts
  useEffect(() => {
    if (!merchantId) return

    // Load user votes from localStorage
    try {
      const storedVotes = localStorage.getItem(`nerava_amenity_votes_${merchantId}`)
      if (storedVotes) {
        setUserAmenityVotes(JSON.parse(storedVotes))
      }
    } catch {
      // Invalid JSON, ignore
    }

    // Initialize amenity counts (default to 0 if not provided by API)
    // Always show amenities (even with 0 votes) so users can vote
    const defaultAmenities = {
      bathroom: { upvotes: 0, downvotes: 0 },
      wifi: { upvotes: 0, downvotes: 0 },
    }
    const apiAmenities = merchantData?.merchant.amenities || defaultAmenities
    setLocalAmenityCounts(apiAmenities)
  }, [merchantId, merchantData])

  // Calculate remaining minutes for display
  const remainingMinutes = Math.ceil(remainingSeconds / 60)

  // Countdown timer when exclusive is active
  useEffect(() => {
    if (flowState !== 'idle' && flowState !== 'completed' && remainingSeconds > 0) {
      const interval = setInterval(() => {
        setRemainingSeconds(prev => Math.max(0, prev - 1))
      }, 1000)
      return () => clearInterval(interval)
    }
  }, [flowState, remainingSeconds])

  const handleActivateExclusive = useCallback(async () => {
    if (!merchantId) {
      setInlineError('Missing merchant ID. Please go back and try again.')
      return
    }

    // TEMPORARY: Location is optional for demo
    // Try to get location but proceed even if it fails
    let lat: number | undefined
    let lng: number | undefined
    let accuracy_m: number | undefined

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        })
      })
      lat = position.coords.latitude
      lng = position.coords.longitude
      accuracy_m = position.coords.accuracy || undefined
      console.log('[Demo] Activating with location:', lat, lng)
    } catch (err) {
      console.log('[Demo] Location unavailable, activating without location:', err)
    }

    try {
      const response = await activateExclusive.mutateAsync({
        merchant_id: merchantId,
        merchant_place_id: merchantId,
        charger_id: chargerId,
        lat: lat ?? null,  // V3: null when unavailable, never 0
        lng: lng ?? null,  // V3: null when unavailable, never 0
        accuracy_m,
      })

      setExclusiveSessionId(response.exclusive_session.id)
      setRemainingSeconds(response.exclusive_session.remaining_seconds)
      setShowActivateModal(false)
      setFlowState('activated') // Show the ExclusiveActivatedModal
    } catch (err) {
      console.error('Failed to activate exclusive:', err)
      setInlineError('Failed to activate exclusive. Please try again.')
    }
  }, [merchantId, chargerId, activateExclusive])

  const handleStartWalking = () => {
    setFlowState('walking')
  }

  const handleViewDetails = () => {
    setFlowState('walking')
  }

  const handleImAtMerchant = async () => {
    if (!exclusiveSessionId) {
      setInlineError('No active exclusive session. Please activate first.')
      return
    }

    try {
      // Get current location for verification
      let lat: number | undefined
      let lng: number | undefined
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          })
        })
        lat = position.coords.latitude
        lng = position.coords.longitude
      } catch {
        // Location failed, proceed without it
        console.log('Could not get location for verification')
      }

      // Call verify endpoint to get verification code
      const response = await verifyVisit.mutateAsync({
        exclusive_session_id: exclusiveSessionId,
        lat,
        lng,
      })

      setVerificationCode(response.verification_code)
      setFlowState('at_merchant')
    } catch (err) {
      setInlineError('Failed to verify visit: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  const handleVerificationDone = () => {
    // Show preferences modal only once per session
    const hasSeenPreferences = sessionStorage.getItem('preferences_modal_shown')
    if (!hasSeenPreferences) {
      setFlowState('preferences')
      sessionStorage.setItem('preferences_modal_shown', 'true')
    } else {
      setFlowState('completed')
    }
  }

  const handlePreferencesClose = () => {
    setFlowState('completed')
  }

  const handleCompletedContinue = async (feedback?: { thumbsUp: boolean }) => {
    // Complete the exclusive session with feedback
    if (exclusiveSessionId) {
      try {
        await completeExclusive.mutateAsync({
          exclusive_session_id: exclusiveSessionId,
          feedback: feedback ? { thumbs_up: feedback.thumbsUp } : undefined,
        })
      } catch (err) {
        console.error('Failed to complete exclusive:', err)
      }
    }

    // Navigate back to main view
    navigate('/wyc')
  }

  const handleAddToSessions = async () => {
    // TEMPORARY: Location is optional for demo - try to get it but don't block if unavailable
    // TODO: Re-enable location requirement after demo period
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000 // Allow cached position up to 1 minute old
        })
      })
      // Log location for analytics but don't block based on it
      console.log('[Demo] Got location:', position.coords.latitude, position.coords.longitude)
    } catch (err) {
      // Location not available - that's okay for demo
      console.log('[Demo] Location not available, proceeding anyway:', err)
    }

    // Proceed to authentication check
    if (!isAuthenticated) {
      setShowActivateModal(true)
    } else {
      await handleActivateExclusive()
    }
  }

  // ============================================
  // V3: "Secure a Spot" flow handlers
  // Only active when FEATURE_FLAGS.SECURE_A_SPOT_V3 is true
  // ============================================

  const handleSecureSpot = () => {
    // If we have a previous intent and compact summary is showing, use it directly
    if (FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 && showCompactIntentSummary && refuelDetails) {
      // Use existing refuelDetails, proceed to authentication
      if (!isAuthenticated) {
        setShowActivateModal(true)
      } else {
        handleActivateWithIntent(refuelDetails)
      }
    } else {
      // Show intent capture modal first
      setShowRefuelIntentModal(true)
    }
  }

  const handleIntentConfirm = (details: RefuelDetails) => {
    setRefuelDetails(details)
    setShowRefuelIntentModal(false)
    setShowCompactIntentSummary(false) // Hide compact summary when new intent is confirmed

    // Proceed to authentication if needed
    if (!isAuthenticated) {
      setShowActivateModal(true)
    } else {
      handleActivateWithIntent(details)
    }
  }

  const handleActivateWithIntent = async (details: RefuelDetails) => {
    if (!merchantId || !merchantData) {
      setInlineError('Missing merchant data. Please go back and try again.')
      return
    }

    // Get location (OPTIONAL for V3)
    let lat: number | null = null
    let lng: number | null = null
    let accuracy_m: number | undefined

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        })
      })
      lat = position.coords.latitude
      lng = position.coords.longitude
      accuracy_m = position.coords.accuracy || undefined
      console.log('[V3] Location acquired:', { lat, lng, accuracy_m })
    } catch (err) {
      // V3: Location is optional, proceed without it
      console.log('[V3] Location unavailable, proceeding with null:', err)
    }

    try {
      const response = await activateExclusive.mutateAsync({
        merchant_id: merchantId,
        // CORRECT: Use actual place_id from merchant data, not merchantId
        merchant_place_id: merchantData.merchant.place_id ?? null,
        charger_id: chargerId,
        lat,  // V3: Can be null
        lng,  // V3: Can be null
        accuracy_m,
        // V3: Intent capture fields
        intent: details.intent,
        party_size: details.partySize,
        needs_power_outlet: details.needsPowerOutlet,
        is_to_go: details.isToGo,
      })

      const sessionId = response.exclusive_session.id
      setExclusiveSessionId(sessionId)
      setRemainingSeconds(response.exclusive_session.remaining_seconds)

      // Generate Reservation ID (V3: client-side only, informational)
      // IMPORTANT: Persist to localStorage keyed by session ID to survive remounts
      const storageKey = `reservation_id_${sessionId}`
      let id = localStorage.getItem(storageKey)
      if (!id) {
        id = generateReservationId(merchantData.merchant.name)
        localStorage.setItem(storageKey, id)
      }
      setReservationId(id)

      setShowActivateModal(false)
      setShowSpotSecuredModal(true)
    } catch (err) {
      console.error('[V3] Failed to secure spot:', err)

      // Clear intent state on error so user can retry
      setRefuelDetails(null)

      if (err instanceof ApiError) {
        if (err.status === 400) {
          setInlineError('Invalid request. Please check your selections and try again.')
        } else if (err.status === 401) {
          setInlineError('Authentication required. Please sign in again.')
          setIsAuthenticated(false)
          setShowActivateModal(true)
        } else if (err.status >= 500) {
          setInlineError('Server error. Please try again in a moment.')
        } else {
          setInlineError('Failed to secure spot. Please try again.')
        }
      } else {
        setInlineError('Network error. Please check your connection and try again.')
      }
    }
  }

  const handleSpotSecuredContinue = () => {
    // Close modal and transition to walking state
    setShowSpotSecuredModal(false)
    setFlowState('walking')
    // V4 TODO: Open sessions modal or navigate to sessions route
  }

  // V3: Cleanup reservation ID from localStorage when session expires or completes
  useEffect(() => {
    if (remainingSeconds !== null && remainingSeconds <= 0) {
      if (exclusiveSessionId) {
        const storageKey = `reservation_id_${exclusiveSessionId}`
        localStorage.removeItem(storageKey)
      }
    }
  }, [remainingSeconds, exclusiveSessionId])

  // Cleanup when transitioning out of session state
  useEffect(() => {
    if (flowState === 'idle' && exclusiveSessionId) {
      const storageKey = `reservation_id_${exclusiveSessionId}`
      localStorage.removeItem(storageKey)
    }
  }, [flowState, exclusiveSessionId])

  const handleGetDirections = () => {
    if (merchantData?.actions.get_directions_url) {
      window.open(merchantData.actions.get_directions_url, '_blank')
    }
  }

  // Amenity voting handler
  const handleAmenityVote = async (amenity: 'bathroom' | 'wifi', voteType: 'up' | 'down') => {
    if (!merchantId || !localAmenityCounts) return

    const previousVote = userAmenityVotes[amenity]
    // Toggle vote if same type clicked, otherwise change vote
    const newVote = previousVote === voteType ? null : voteType

    // Optimistic update: update UI immediately
    const updatedVotes = {
      ...userAmenityVotes,
      [amenity]: newVote,
    }
    setUserAmenityVotes(updatedVotes)

    // Update local counts optimistically
    const newCounts = { ...localAmenityCounts }
    const amenityData = { ...newCounts[amenity] }

    // Remove previous vote if exists
    if (previousVote === 'up') {
      amenityData.upvotes = Math.max(0, amenityData.upvotes - 1)
    } else if (previousVote === 'down') {
      amenityData.downvotes = Math.max(0, amenityData.downvotes - 1)
    }

    // Add new vote if not removing
    if (newVote === 'up') {
      amenityData.upvotes += 1
    } else if (newVote === 'down') {
      amenityData.downvotes += 1
    }

    newCounts[amenity] = amenityData
    setLocalAmenityCounts(newCounts)

    // Check feature flag for API usage
    const useApi = import.meta.env.VITE_USE_AMENITY_VOTES_API === 'true'

    if (useApi && merchantId) {
      try {
        // Call API
        const response = await voteAmenityMutation.mutateAsync({
          merchantId,
          amenity,
          voteType,
        })

        // Update counts from API response
        setLocalAmenityCounts({
          ...newCounts,
          [amenity]: {
            upvotes: response.upvotes,
            downvotes: response.downvotes,
          },
        })
      } catch (error) {
        // API failed: rollback optimistic update and use localStorage fallback
        console.warn('[AmenityVote] API call failed, falling back to localStorage:', error)
        
        // Rollback optimistic update
        setUserAmenityVotes(userAmenityVotes)
        setLocalAmenityCounts(localAmenityCounts)
      }
    } else {
      // Feature flag disabled: use localStorage only
      localStorage.setItem(`nerava_amenity_votes_${merchantId}`, JSON.stringify(updatedVotes))
    }

    // Close modal
    setShowAmenityVoteModal(false)
  }

  if (isLoading) {
    return <MerchantDetailsSkeleton />
  }

  if (error || !merchantData) {
    return (
      <div className="flex items-center justify-center bg-gray-50 p-4" style={{ height: 'var(--app-height, 100dvh)' }}>
        <div className="text-center">
          <p className="text-gray-900 font-medium mb-2">Merchant not found</p>
          <p className="text-gray-600 text-sm">{error?.message || 'Unknown error'}</p>
        </div>
      </div>
    )
  }

  const photoUrls = (merchantData.merchant as any).photo_urls
  const walkTime = merchantData.moment.label
  const isExclusive = merchantData.perk?.badge === 'Exclusive'
  const isActiveState = flowState === 'walking'

  return (
    <div className="bg-white overflow-y-auto" style={{ height: 'var(--app-height, 100dvh)' }}>
      {/* Hero image */}
      <HeroImageHeader
        photoUrls={photoUrls}
        photoUrl={merchantData.merchant.photo_url || photoFromNav}
        merchantName={merchantData.merchant.name}
        category={merchantData.merchant.category}
        walkTime={isActiveState ? `${remainingMinutes} minutes remaining` : walkTime}
        isExclusive={isExclusive}
        isExclusiveActive={isActiveState}
        onClose={() => navigate(-1)}
        onFavorite={() => {}}
        onShare={() => {}}
      />

      {/* Content */}
      <div className="px-4 py-6 space-y-5">
        {/* Merchant name and category */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 leading-tight mb-2">{merchantData.merchant.name}</h1>
          <p className="text-base text-gray-600">{merchantData.merchant.category}</p>
          {/* Social Proof Badge and Amenity Votes */}
          <div className="mt-3 flex items-start justify-between gap-3">
            <SocialProofBadge
              neravaSessionsCount={(merchantData.merchant as any).neravaSessionsCount}
              activeDriversCount={(merchantData.merchant as any).activeDriversCount}
            />
            <AmenityVotes
              bathroom={localAmenityCounts?.bathroom || { upvotes: 0, downvotes: 0 }}
              wifi={localAmenityCounts?.wifi || { upvotes: 0, downvotes: 0 }}
              interactive={false}
              userVotes={userAmenityVotes}
              onAmenityClick={(amenity) => {
                setSelectedAmenity(amenity)
                setShowAmenityVoteModal(true)
              }}
            />
          </div>
        </div>

        {/* Walk instruction when active */}
        {isActiveState && (
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <p className="text-gray-700">
              Walk to {merchantData.merchant.name} and show this screen
            </p>
          </div>
        )}

        {/* Exclusive Offer Card */}
        {merchantData.perk && (
          <ExclusiveOfferCard
            title={merchantData.perk.title}
            description={merchantData.perk.description}
          />
        )}

        {/* Distance card */}
        <DistanceCard
          distanceMiles={merchantData.moment.distance_miles}
          walkTimeLabel={walkTime}
        />

        {/* Hours card */}
        <HoursCard />

        {/* Description */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-700 leading-relaxed">
            {merchantData.perk?.description ?? merchantData.merchant.description ?? ''}
          </p>
        </div>

        {/* Get Directions button */}
        <Button
          variant="secondary"
          className="w-full"
          onClick={handleGetDirections}
        >
          Get Directions
        </Button>

        {/* Compact Intent Summary - Progressive disclosure when previous intent exists */}
        {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 && FEATURE_FLAGS.SECURE_A_SPOT_V3 && showCompactIntentSummary && refuelDetails && flowState === 'idle' && merchantData.wallet.can_add && (
          <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-3 border border-[#E4E6EB]">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-[#65676B] mb-1">Your intent</p>
                <p className="text-sm font-medium text-[#050505]">
                  {refuelDetails.intent === 'eat' 
                    ? `Dining, Party of ${refuelDetails.partySize || 2}`
                    : refuelDetails.intent === 'work'
                    ? `Work Session${refuelDetails.needsPowerOutlet ? ' + Power' : ''}`
                    : `Quick Stop${refuelDetails.isToGo ? ' (To-Go)' : ''}`
                  }
                </p>
              </div>
              <button
                onClick={() => {
                  setShowCompactIntentSummary(false)
                  setShowRefuelIntentModal(true)
                }}
                className="text-sm text-[#1877F2] font-medium hover:underline ml-4"
              >
                Change
              </button>
            </div>
          </div>
        )}

        {/* Inline error — replaces browser alert() */}
        <InlineError
          message={inlineError}
          onDismiss={() => setInlineError(null)}
        />

        {/* Main action button based on state */}
        {flowState === 'idle' && merchantData.wallet.can_add && (
          <Button
            variant="primary"
            className="w-full"
            onClick={FEATURE_FLAGS.SECURE_A_SPOT_V3 ? handleSecureSpot : handleAddToSessions}
            disabled={activateExclusive.isPending}
          >
            {activateExclusive.isPending
              ? (FEATURE_FLAGS.SECURE_A_SPOT_V3 ? 'Securing...' : 'Activating...')
              : (FEATURE_FLAGS.SECURE_A_SPOT_V3 ? 'Secure a Spot' : 'Activate Exclusive')
            }
          </Button>
        )}

        {isActiveState && (
          <Button
            variant="primary"
            className="w-full"
            onClick={handleImAtMerchant}
            disabled={verifyVisit.isPending}
          >
            {verifyVisit.isPending ? 'Verifying...' : "I'm at the Merchant"}
          </Button>
        )}
      </div>

      {/* Modals based on flow state */}

      {/* OTP Activate Modal */}
      <ActivateExclusiveModal
        isOpen={showActivateModal}
        onClose={() => setShowActivateModal(false)}
        onSuccess={async () => {
          setIsAuthenticated(true)
          setShowActivateModal(false)
          // V3: Use intent flow if flag enabled and intent was captured
          if (FEATURE_FLAGS.SECURE_A_SPOT_V3 && refuelDetails) {
            await handleActivateWithIntent(refuelDetails)
          } else {
            await handleActivateExclusive()
          }
        }}
      />

      {/* Exclusive Activated Modal */}
      {flowState === 'activated' && merchantData && (
        <ExclusiveActivatedModal
          merchantName={merchantData.merchant.name}
          perkTitle={merchantData.perk?.title ?? 'Exclusive Offer'}
          remainingMinutes={remainingMinutes}
          onStartWalking={handleStartWalking}
          onViewDetails={handleViewDetails}
        />
      )}

      {/* Verification Code Modal */}
      {flowState === 'at_merchant' && verificationCode && merchantData && (
        <VerificationCodeModal
          merchantName={merchantData.merchant.name}
          verificationCode={verificationCode}
          onDone={handleVerificationDone}
        />
      )}

      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={flowState === 'preferences'}
        onClose={handlePreferencesClose}
      />

      {/* Exclusive Completed Modal */}
      {flowState === 'completed' && (
        <ExclusiveCompletedModal
          onContinue={handleCompletedContinue}
        />
      )}

      {/* V3: Refuel Intent Modal (only when feature flag enabled) */}
      {FEATURE_FLAGS.SECURE_A_SPOT_V3 && (
        <RefuelIntentModal
          merchantName={merchantData?.merchant.name || ''}
          isOpen={showRefuelIntentModal}
          onClose={() => setShowRefuelIntentModal(false)}
          onConfirm={handleIntentConfirm}
        />
      )}

      {/* V3: Spot Secured Modal (only when feature flag enabled) */}
      {FEATURE_FLAGS.SECURE_A_SPOT_V3 && refuelDetails && reservationId && merchantData && (
        <SpotSecuredModal
          merchantName={merchantData.merchant.name}
          merchantBadge={merchantData.perk?.badge}
          refuelDetails={refuelDetails}
          remainingMinutes={remainingMinutes}
          reservationId={reservationId}
          isOpen={showSpotSecuredModal}
          onContinue={handleSpotSecuredContinue}
        />
      )}

      {/* Amenity Vote Modal */}
      {showAmenityVoteModal && selectedAmenity && localAmenityCounts && merchantData && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl">
            {/* Title */}
            <h2 className="text-xl text-center mb-4">
              Rate {selectedAmenity === 'bathroom' ? 'Bathroom' : 'WiFi'}
            </h2>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              How was the {selectedAmenity === 'bathroom' ? 'bathroom' : 'WiFi'} at {merchantData.merchant.name}?
            </p>

            {/* Vote Buttons */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => handleAmenityVote(selectedAmenity, 'up')}
                className={`flex-1 py-4 rounded-2xl font-medium transition-all flex items-center justify-center gap-2 ${
                  userAmenityVotes[selectedAmenity] === 'up'
                    ? 'bg-green-100 text-green-700 border-2 border-green-500'
                    : 'bg-[#F7F8FA] text-[#050505] border-2 border-[#E4E6EB] hover:border-green-500'
                }`}
                aria-label="Vote good"
              >
                <ThumbsUp className="w-5 h-5" />
                Good
              </button>
              <button
                onClick={() => handleAmenityVote(selectedAmenity, 'down')}
                className={`flex-1 py-4 rounded-2xl font-medium transition-all flex items-center justify-center gap-2 ${
                  userAmenityVotes[selectedAmenity] === 'down'
                    ? 'bg-red-100 text-red-700 border-2 border-red-500'
                    : 'bg-[#F7F8FA] text-[#050505] border-2 border-[#E4E6EB] hover:border-red-500'
                }`}
                aria-label="Vote bad"
              >
                <ThumbsDown className="w-5 h-5" />
                Bad
              </button>
            </div>

            {/* Cancel Button */}
            <button
              onClick={() => setShowAmenityVoteModal(false)}
              className="w-full py-3 bg-white border border-[#E4E6EB] text-[#65676B] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
