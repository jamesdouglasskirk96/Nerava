// DriverHome - Main orchestrator component for driver app
import { useState, useEffect } from 'react'
import { Zap } from 'lucide-react'
import { useDriverSessionContext } from '../../contexts/DriverSessionContext'
import { useFavorites } from '../../contexts/FavoritesContext'
import { useExclusiveSessionState } from '../../hooks/useExclusiveSessionState'
import { useIntentCapture, useWalletActivate, useExclusiveActivate, useExclusiveComplete, useShareLink } from '../../services/api'
import { useFavoriteMerchant } from '../../hooks/useFavoriteMerchant'
import { ApiError } from '../../services/api'
import { MerchantCarousel } from '../MerchantCarousel/MerchantCarousel'
import { ExclusiveActiveView } from '../ExclusiveActiveView/ExclusiveActiveView'
import { MerchantDetailModal } from '../MerchantDetail/MerchantDetailModal'
import { ActivateExclusiveModal } from '../ActivateExclusiveModal/ActivateExclusiveModal'
import { ArrivalConfirmationModal } from '../ArrivalConfirmationModal/ArrivalConfirmationModal'
import { CompletionFeedbackModal } from '../CompletionFeedbackModal/CompletionFeedbackModal'
import { PreferencesModal } from '../Preferences/PreferencesModal'
import { PreChargingScreen } from '../PreCharging/PreChargingScreen'
import { WhileYouChargeScreen } from '../WhileYouCharge/WhileYouChargeScreen'
import { useChargerState } from '../../hooks/useChargerState'
import { groupMerchantsIntoSets, groupChargersIntoSets } from '../../utils/dataMapping'
import { getMerchantSets, mockMerchants } from '../../mock/mockMerchants'
import { getChargerSetsWithExperiences } from '../../mock/mockChargers'
import { isMockMode } from '../../services/api'
import type { MockMerchant } from '../../mock/mockMerchants'
import type { MockCharger } from '../../mock/mockChargers'
import type { ExclusiveMerchant } from '../../hooks/useExclusiveSessionState'

/**
 * Main entry point that orchestrates the three states:
 * - PRE_CHARGING: User not within charger radius
 * - CHARGING_ACTIVE: User within charger radius
 * - EXCLUSIVE_ACTIVE: User has activated an exclusive
 */
export function DriverHome() {
  const {
    locationPermission,
    locationFix,
    coordinates,
    appChargingState,
    sessionId,
    setAppChargingState,
    setSessionId,
    setActiveExclusive: setDriverSessionExclusive,
  } = useDriverSessionContext()
  const { activeExclusive, remainingMinutes, activateExclusive, clearExclusive } = useExclusiveSessionState()
  const _walletActivateMutation = useWalletActivate()
  const exclusiveActivateMutation = useExclusiveActivate()
  const exclusiveCompleteMutation = useExclusiveComplete()
  
  // Use charger discovery state hook
  const { showCharging, nearestChargerId, chargers, loading: chargerLoading } = useChargerState()

  const [currentSetIndex, setCurrentSetIndex] = useState(0)
  const [selectedMerchant, setSelectedMerchant] = useState<MockMerchant | null>(null)
  const [showActivateModal, setShowActivateModal] = useState(false)
  const [showArrivalModal, setShowArrivalModal] = useState(false)
  const [showCompletionModal, setShowCompletionModal] = useState(false)
  const [showPreferencesModal, setShowPreferencesModal] = useState(false)
  const { favoriteIds, toggleFavorite } = useFavorites()
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    // Check if user has access token
    return !!localStorage.getItem('access_token')
  })

  // Intent capture request - only when location is available and not in EXCLUSIVE_ACTIVE
  const intentRequest =
    coordinates && appChargingState !== 'EXCLUSIVE_ACTIVE'
      ? {
          lat: coordinates.lat,
          lng: coordinates.lng,
          accuracy_m: coordinates.accuracy_m,
          client_ts: new Date().toISOString(),
        }
      : null

  const { data: intentData, isLoading: intentLoading } = useIntentCapture(intentRequest)

  // Store session_id when intent capture succeeds
  useEffect(() => {
    if (intentData?.session_id && intentData.session_id !== sessionId) {
      setSessionId(intentData.session_id)
    }
  }, [intentData?.session_id, sessionId, setSessionId])

  // Determine which data to use (mock or real)
  const useMockData = isMockMode()
  
  // Only load mock data if explicitly in mock mode
  const mockMerchantSets = useMockData ? getMerchantSets() : []
  const mockChargerSets = useMockData ? getChargerSetsWithExperiences() : []

  // Real data from intent capture
  const realMerchantSets = intentData?.merchants
    ? groupMerchantsIntoSets(intentData.merchants)
    : []
  const realChargerSets = intentData?.charger_summary
    ? groupChargersIntoSets(intentData.charger_summary, intentData.merchants || [])
    : []

  // In production, use real data only - don't fall back to mock
  const merchantSets = useMockData ? mockMerchantSets : realMerchantSets
  const chargerSets = useMockData ? mockChargerSets : realChargerSets

  // Use charger sets in PRE_CHARGING mode, merchant sets in CHARGING_ACTIVE mode
  const activeSets = appChargingState === 'PRE_CHARGING' ? chargerSets : merchantSets
  const currentSet = activeSets[currentSetIndex] || (appChargingState === 'PRE_CHARGING'
    ? { featured: chargerSets[0]?.featured, nearby: [] }
    : { featured: undefined, nearby: [] })

  // Determine if user is in charger radius (for PRE_CHARGING state)
  const isInChargerRadius =
    appChargingState === 'CHARGING_ACTIVE' ||
    (intentData?.charger_summary && intentData.charger_summary.distance_m < 150) ||
    (intentData?.confidence_tier === 'A')

  const handleMerchantClick = (item: MockMerchant | MockCharger) => {
    // Only set selected merchant if it's actually a merchant (not a charger)
    if ('isSponsored' in item || 'badges' in item) {
      setSelectedMerchant(item as MockMerchant)
    }
    // For chargers, we could navigate to charger detail in the future
  }

  const handleCloseMerchantDetails = () => {
    setSelectedMerchant(null)
  }

  const handleActivateExclusive = (merchant: MockMerchant) => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      // Show OTP modal first
      setShowActivateModal(true)
    } else {
      // User is already authenticated, proceed directly to activation
      handleActivateExclusiveDirect(merchant)
    }
  }

  const handleActivateExclusiveDirect = async (merchant: MockMerchant) => {
    // Check if user has access token
    const accessToken = localStorage.getItem('access_token')
    if (!accessToken) {
      // Should not happen if OTP flow worked, but double-check
      setShowActivateModal(true)
      return
    }

    // Convert MockMerchant to ExclusiveMerchant
    const exclusiveMerchant: ExclusiveMerchant = {
      id: merchant.id,
      name: merchant.name,
      category: merchant.category,
      walkTime: merchant.walkTime,
      imageUrl: merchant.imageUrl,
      badge: merchant.badges?.includes('Exclusive') ? '⭐ Exclusive' : undefined,
      distance: merchant.distance,
      hours: merchant.hours,
      hoursStatus: merchant.hoursStatus,
      description: merchant.description,
      exclusiveOffer: merchant.exclusiveOffer,
    }

    // Call backend to activate exclusive
    if (!isMockMode() && coordinates) {
      try {
        // Get charger_id from intent data or use a default for party flow
        const chargerId = intentData?.charger_summary?.id || 'asadas_party_charger'
        
        const response = await exclusiveActivateMutation.mutateAsync({
          merchant_id: merchant.id,
          charger_id: chargerId,
          lat: coordinates.lat,
          lng: coordinates.lng,
          accuracy_m: coordinates.accuracy_m,
        })
        
        // Only show ACTIVE if backend confirms
        if (response.status === 'ACTIVE' && response.exclusive_session) {
          const expiresAt = new Date(response.exclusive_session.expires_at)
          // Store session ID for completion
          localStorage.setItem('nerava_exclusive_session_id', response.exclusive_session.id)
          setDriverSessionExclusive(response.exclusive_session.merchant_id || merchant.id, expiresAt.toISOString())
          activateExclusive(exclusiveMerchant, expiresAt.toISOString())
        } else {
          console.error('Backend did not return ACTIVE status:', response)
          throw new Error('Activation failed')
        }
      } catch (error) {
        console.error('Failed to activate exclusive:', error)
        
        // Handle 428 OTP_REQUIRED or 401 Unauthorized
        if (error instanceof ApiError) {
          if (error.status === 428 || error.code === 'OTP_REQUIRED') {
            // OTP required - show modal again
            setIsAuthenticated(false)
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            setShowActivateModal(true)
            return
          } else if (error.status === 401) {
            // Token expired/invalid - clear auth and show OTP modal
            setIsAuthenticated(false)
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            setShowActivateModal(true)
            return
          }
        }
        
        // For other errors, show error but don't activate
        alert('Failed to activate exclusive. Please try again.')
        return
      }
    } else {
      // Mock mode or no coordinates - use local activation
      activateExclusive(exclusiveMerchant)
    }

    setShowActivateModal(false)
    setSelectedMerchant(null)
  }

  const handleOTPSuccess = () => {
    // User successfully authenticated (tokens stored in auth.ts)
    setIsAuthenticated(true)
    setShowActivateModal(false)

    // Automatically retry exclusive activation if merchant is selected
    if (selectedMerchant) {
      // Small delay to ensure tokens are stored
      setTimeout(() => {
        handleActivateExclusiveDirect(selectedMerchant)
      }, 100)
    }
  }

  const handleOTPClose = () => {
    setShowActivateModal(false)
  }

  const handleArrived = async () => {
    // Get the exclusive session ID from localStorage or state
    // The session ID should be stored when exclusive is activated
    const sessionId = localStorage.getItem('nerava_exclusive_session_id')
    
    if (sessionId && !isMockMode()) {
      try {
        await exclusiveCompleteMutation.mutateAsync({
          exclusive_session_id: sessionId,
        })
        // Success - show arrival modal
        setShowArrivalModal(true)
      } catch (error) {
        console.error('Failed to complete exclusive:', error)
        // Still show arrival modal even if complete fails
        setShowArrivalModal(true)
      }
    } else {
      // Mock mode or no session ID - just show arrival modal
      setShowArrivalModal(true)
    }
  }

  const handleArrivalDone = () => {
    setShowArrivalModal(false)
    setShowCompletionModal(true)
  }

  const handleCompletionContinue = () => {
    setShowCompletionModal(false)
    setShowPreferencesModal(true)
  }

  const handlePreferencesDone = () => {
    setShowPreferencesModal(false)
    // Reset state and return to discovery
    clearExclusive()
    // Return to appropriate state
    if (appChargingState === 'CHARGING_ACTIVE') {
      // Stay in CHARGING_ACTIVE
    } else {
      // Return to PRE_CHARGING
    }
  }

  const handlePrevSet = () => {
    setCurrentSetIndex((prev) => (prev === 0 ? merchantSets.length - 1 : prev - 1))
  }

  const handleNextSet = () => {
    setCurrentSetIndex((prev) => (prev === merchantSets.length - 1 ? 0 : prev + 1))
  }

  const handleToggleCharging = () => {
    if (appChargingState === 'PRE_CHARGING') {
      setAppChargingState('CHARGING_ACTIVE')
    } else {
      setAppChargingState('PRE_CHARGING')
    }
    setCurrentSetIndex(0)
    setSelectedMerchant(null)
    // Reset exclusive state when switching modes
    clearExclusive()
  }

  // State-based headline and subheadline
  const headline = 'What to do while you charge'
  const subheadline =
    appChargingState === 'CHARGING_ACTIVE'
      ? 'Curated access, active while charging'
      : 'Personalized access during your charge window'

  // Dev console logging (only in development)
  useEffect(() => {
    if (import.meta.env.DEV) {
      console.group('Nerava Integration')
      console.log('Mock mode:', isMockMode())
      console.log('API base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001')
      console.log('Location permission:', locationPermission)
      console.log('Location fix:', locationFix)
      console.log('Coordinates:', coordinates)
      console.log('App charging state:', appChargingState)
      console.log('Session ID:', sessionId)
      console.log('Intent capture loading:', intentLoading)
      console.log('Intent data:', intentData)
      console.groupEnd()
    }
  }, [locationPermission, locationFix, coordinates, appChargingState, sessionId, intentLoading, intentData])

  // If exclusive is active, show exclusive view
  if (activeExclusive) {
    const { isFavorite, toggleFavorite } = useFavoriteMerchant(activeExclusive.id)
    const { data: shareData } = useShareLink(activeExclusive.id)
    
    const handleShare = async () => {
      if (shareData) {
        // Use Web Share API if available (mobile)
        if (navigator.share) {
          try {
            await navigator.share({
              title: shareData.title,
              text: shareData.description,
              url: shareData.url,
            })
          } catch (err) {
            // User cancelled or error - fall back to clipboard
            if (err instanceof Error && err.name !== 'AbortError') {
              navigator.clipboard.writeText(shareData.url)
              alert('Link copied to clipboard!')
            }
          }
        } else {
          // Fallback: copy to clipboard
          navigator.clipboard.writeText(shareData.url)
          alert('Link copied to clipboard!')
        }
      } else {
        // Fallback if share data not loaded
        const url = `https://app.nerava.network/merchant/${activeExclusive.id}`
        navigator.clipboard.writeText(url)
        alert('Link copied to clipboard!')
      }
    }
    
    return (
      <>
        <ExclusiveActiveView
          merchant={activeExclusive}
          remainingMinutes={remainingMinutes}
          onArrived={handleArrived}
          onToggleLike={toggleFavorite}
          onShare={handleShare}
          isLiked={isFavorite}
        />
        <ArrivalConfirmationModal
          isOpen={showArrivalModal}
          merchantName={activeExclusive.name}
          exclusiveBadge={activeExclusive.badge}
          onDone={handleArrivalDone}
        />
        <CompletionFeedbackModal
          isOpen={showCompletionModal}
          onContinue={handleCompletionContinue}
        />
        <PreferencesModal
          isOpen={showPreferencesModal}
          onClose={handlePreferencesDone}
        />
      </>
    )
  }

  // Discovery View - Conditionally render PreChargingScreen or WhileYouChargeScreen
  // Use charger discovery state to determine which screen to show
  if (showCharging && nearestChargerId) {
    // User is within 400m of a charger - show charging experience
    return (
      <>
        <WhileYouChargeScreen chargerId={nearestChargerId} />
        {/* Merchant Details Modal */}
        {selectedMerchant && (
          <MerchantDetailModal
            merchant={selectedMerchant}
            isCharging={true}
            isInChargerRadius={true}
            onClose={handleCloseMerchantDetails}
            onToggleLike={(id) => toggleFavorite(id)}
            onActivateExclusive={handleActivateExclusive}
            likedMerchants={favoriteIds}
          />
        )}
        {/* Activation Modal (OTP) */}
        <ActivateExclusiveModal
          isOpen={showActivateModal}
          onClose={handleOTPClose}
          onSuccess={handleOTPSuccess}
          merchantId={selectedMerchant?.id}
          chargerId={nearestChargerId}
        />
        {/* Preferences Modal */}
        <PreferencesModal
          isOpen={showPreferencesModal}
          onClose={handlePreferencesDone}
        />
      </>
    )
  }
  
  // User is outside 400m radius - show charger discovery
  return (
    <>
      <PreChargingScreen chargers={chargers} loading={chargerLoading} />
      {/* Merchant Details Modal */}
      {selectedMerchant && (
        <MerchantDetailModal
          merchant={selectedMerchant}
          isCharging={false}
          isInChargerRadius={false}
          onClose={handleCloseMerchantDetails}
          onToggleLike={(id) => toggleFavorite(id)}
          onActivateExclusive={handleActivateExclusive}
          likedMerchants={favoriteIds}
        />
      )}
      {/* Activation Modal (OTP) */}
      <ActivateExclusiveModal
        isOpen={showActivateModal}
        onClose={handleOTPClose}
        onSuccess={handleOTPSuccess}
        merchantId={selectedMerchant?.id}
        chargerId={nearestChargerId || 'canyon_ridge_supercharger'}
      />
      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={showPreferencesModal}
        onClose={handlePreferencesDone}
      />
    </>
  )
}

