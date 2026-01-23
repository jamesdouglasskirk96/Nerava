// DriverHome - Main orchestrator component for driver app
import { useState, useEffect, useRef } from 'react'
import { Zap } from 'lucide-react'
import { useDriverSessionContext } from '../../contexts/DriverSessionContext'
import { useExclusiveSessionState } from '../../hooks/useExclusiveSessionState'
import {
  useIntentCapture,
  useActivateExclusive,
  useCompleteExclusive,
  useActiveExclusive,
  useLocationCheck,
  checkLocation,
} from '../../services/api'
import { useChargingState } from '../../hooks/useChargingState'
import { capture, page, DRIVER_EVENTS } from '../../analytics'
import { MerchantCarousel } from '../MerchantCarousel/MerchantCarousel'
import { ExclusiveActiveView } from '../ExclusiveActiveView/ExclusiveActiveView'
import { MerchantDetailModal } from '../MerchantDetail/MerchantDetailModal'
import { ActivateExclusiveModal } from '../ActivateExclusiveModal/ActivateExclusiveModal'
import { ArrivalConfirmationModal } from '../ArrivalConfirmationModal/ArrivalConfirmationModal'
import { CompletionFeedbackModal } from '../CompletionFeedbackModal/CompletionFeedbackModal'
import { PreferencesModal } from '../Preferences/PreferencesModal'
import { AnalyticsDebugPanel } from '../Debug/AnalyticsDebugPanel'
import { groupMerchantsIntoSets, groupChargersIntoSets } from '../../utils/dataMapping'
import { getMerchantSets, mockMerchants } from '../../mock/mockMerchants'
import { getChargerSetsWithExperiences } from '../../mock/mockChargers'
import { isMockMode, isDemoMode } from '../../services/api'
import { ErrorBanner } from '../shared/ErrorBanner'
import { Badge } from '../shared/Badge'
import { LocationDeniedScreen } from '../LocationDenied/LocationDeniedScreen'
import { StateTransitionToast } from '../shared/StateTransitionToast'
import type { MockMerchant } from '../../mock/mockMerchants'
import type { MockCharger } from '../../mock/mockChargers'
import type { ExclusiveMerchant } from '../../hooks/useExclusiveSessionState'
import type { AppChargingState } from '../../contexts/DriverSessionContext'

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
    requestLocationPermission,
  } = useDriverSessionContext()
  const { activeExclusive, remainingMinutes, activateExclusive: activateExclusiveLocal, clearExclusive } = useExclusiveSessionState()
  const activateExclusiveMutation = useActivateExclusive()
  const completeExclusiveMutation = useCompleteExclusive()
  const { data: activeExclusiveData } = useActiveExclusive()
  const chargingState = useChargingState()

  const [currentSetIndex, setCurrentSetIndex] = useState(0)
  const [selectedMerchant, setSelectedMerchant] = useState<MockMerchant | null>(null)
  const [showActivateModal, setShowActivateModal] = useState(false)
  const [showArrivalModal, setShowArrivalModal] = useState(false)
  const [showCompletionModal, setShowCompletionModal] = useState(false)
  const [showPreferencesModal, setShowPreferencesModal] = useState(false)
  const [likedMerchants, setLikedMerchants] = useState<Set<string>>(() => {
    // Load liked merchants from localStorage on mount
    const storedLikes = localStorage.getItem('neravaLikes')
    if (storedLikes) {
      try {
        return new Set(JSON.parse(storedLikes) as string[])
      } catch {
        // Invalid JSON, start fresh
      }
    }
    return new Set()
  })
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    // Check if user has access token
    return !!localStorage.getItem('access_token')
  })
  const [browseMode, setBrowseMode] = useState(false)
  const [showTransitionToast, setShowTransitionToast] = useState(false)
  const lastChargingStateRef = useRef<AppChargingState>(appChargingState)

  // Default center for browse mode (Austin, TX)
  const DEFAULT_CENTER = { lat: 30.2672, lng: -97.7431, accuracy_m: 0, last_fix_ts: Date.now() }
  
  // Use coordinates or default center in browse mode
  const effectiveCoordinates = coordinates || (browseMode ? DEFAULT_CENTER : null)

  // Intent capture request - only when location is available (or browse mode) and not in EXCLUSIVE_ACTIVE
  const intentRequest =
    effectiveCoordinates && chargingState.state !== 'EXCLUSIVE_ACTIVE'
      ? {
          lat: effectiveCoordinates.lat,
          lng: effectiveCoordinates.lng,
          accuracy_m: effectiveCoordinates.accuracy_m,
          client_ts: new Date().toISOString(),
        }
      : null

  const { data: intentData, isLoading: intentLoading, error: intentError, refetch: refetchIntent } = useIntentCapture(intentRequest)
  
  // Capture intent capture request when coordinates become available
  useEffect(() => {
    if (intentRequest && !intentLoading && !intentData) {
      capture(DRIVER_EVENTS.INTENT_CAPTURE_REQUEST, {
        location_accuracy: coordinates?.accuracy_m,
      })
    }
  }, [intentRequest, intentLoading, intentData, coordinates])

  // Store session_id when intent capture succeeds
  useEffect(() => {
    if (intentData?.session_id && intentData.session_id !== sessionId) {
      setSessionId(intentData.session_id)
      capture(DRIVER_EVENTS.INTENT_CAPTURE_SUCCESS, {
        session_id: intentData.session_id,
        location_accuracy: coordinates?.accuracy_m,
        merchant_count: intentData.merchants?.length || 0,
      })
    }
  }, [intentData?.session_id, sessionId, setSessionId, coordinates, intentData])
  
  // Capture page view on mount
  useEffect(() => {
    page('home')
  }, [])
  
  // Capture location permission events
  useEffect(() => {
    if (locationPermission === 'granted') {
      capture(DRIVER_EVENTS.LOCATION_PERMISSION_GRANTED)
    } else if (locationPermission === 'denied') {
      capture(DRIVER_EVENTS.LOCATION_PERMISSION_DENIED)
    }
  }, [locationPermission])

  // Determine which data to use (mock or real)
  const useMockData = isMockMode()
  const useDemoData = isDemoMode()
  const mockMerchantSets = getMerchantSets()
  const mockChargerSets = getChargerSetsWithExperiences()

  // Real data from intent capture
  const realMerchantSets = intentData?.merchants
    ? groupMerchantsIntoSets(intentData.merchants)
    : []
  const realChargerSets = intentData?.charger_summary
    ? groupChargersIntoSets(intentData.charger_summary, intentData.merchants || [])
    : []

  // Use mock data only if explicitly in mock mode OR if demo mode is enabled and API failed
  // Otherwise, use real data only (no silent fallback)
  const hasApiError = intentError !== null && intentError !== undefined
  const merchantSets = useMockData || (useDemoData && hasApiError && realMerchantSets.length === 0)
    ? mockMerchantSets
    : realMerchantSets
  const chargerSets = useMockData || (useDemoData && hasApiError && realChargerSets.length === 0)
    ? mockChargerSets
    : realChargerSets

  // Use charger sets in PRE_CHARGING mode, merchant sets in CHARGING_ACTIVE mode
  const activeSets = appChargingState === 'PRE_CHARGING' ? chargerSets : merchantSets
  const currentSet = activeSets[currentSetIndex] || (appChargingState === 'PRE_CHARGING'
    ? { featured: chargerSets[0]?.featured || mockChargerSets[0]?.featured, nearby: [] }
    : { featured: mockMerchants[0], nearby: [] })

  // Determine if user is in charger radius (for PRE_CHARGING state)
  const isInChargerRadius =
    appChargingState === 'CHARGING_ACTIVE' ||
    (intentData?.charger_summary && intentData.charger_summary.distance_m < 150) ||
    (intentData?.confidence_tier === 'A')

  // Save liked merchants to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('neravaLikes', JSON.stringify(Array.from(likedMerchants)))
  }, [likedMerchants])

  const handleToggleLike = (merchantId: string) => {
    setLikedMerchants((prev) => {
      const newLikes = new Set(prev)
      if (newLikes.has(merchantId)) {
        newLikes.delete(merchantId)
      } else {
        newLikes.add(merchantId)
      }
      return newLikes
    })
  }

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
      setSelectedMerchant(merchant)
      setShowActivateModal(true)
    } else {
      // User is already authenticated, proceed directly to activation
      handleActivateExclusiveDirect(merchant)
    }
  }

  // Check location and update charging state
  const locationCheck = useLocationCheck(coordinates?.lat || null, coordinates?.lng || null)
  
  useEffect(() => {
    if (locationCheck.data && coordinates) {
      if (locationCheck.data.in_charger_radius && chargingState.state === 'PRE_CHARGING') {
        // Detect transition from PRE_CHARGING to CHARGING_ACTIVE
        if (lastChargingStateRef.current === 'PRE_CHARGING') {
          setShowTransitionToast(true)
        }
        chargingState.transitionTo('CHARGING_ACTIVE')
        setAppChargingState('CHARGING_ACTIVE')
        lastChargingStateRef.current = 'CHARGING_ACTIVE'
      } else if (!locationCheck.data.in_charger_radius && chargingState.state === 'CHARGING_ACTIVE' && !activeExclusive) {
        chargingState.transitionTo('PRE_CHARGING')
        setAppChargingState('PRE_CHARGING')
        lastChargingStateRef.current = 'PRE_CHARGING'
      }
    }
  }, [locationCheck.data, coordinates, chargingState, activeExclusive, setAppChargingState])
  
  // Update ref when appChargingState changes (for initial load and manual toggles)
  useEffect(() => {
    lastChargingStateRef.current = appChargingState
  }, [appChargingState])

  // Sync active exclusive from backend
  useEffect(() => {
    if (activeExclusiveData?.exclusive_session) {
      const session = activeExclusiveData.exclusive_session
      if (!activeExclusive) {
        // Convert backend session to ExclusiveMerchant
        const exclusiveMerchant: ExclusiveMerchant = {
          id: session.merchant_id || '',
          name: '', // Will be populated from merchant details
          walkTime: '5 min',
          expiresAt: session.expires_at,
        }
        activateExclusiveLocal(exclusiveMerchant, session.expires_at)
        chargingState.transitionTo('EXCLUSIVE_ACTIVE')
        setAppChargingState('EXCLUSIVE_ACTIVE')
      }
    } else if (activeExclusiveData?.exclusive_session === null && activeExclusive) {
      // Session expired or completed
      clearExclusive()
      chargingState.transitionTo('CHARGING_ACTIVE')
      setAppChargingState('CHARGING_ACTIVE')
    }
  }, [activeExclusiveData, activeExclusive, activateExclusiveLocal, clearExclusive, chargingState, setAppChargingState])

  const handleActivateExclusiveDirect = async (merchant: MockMerchant) => {
    // Check charger radius guard
    if (!coordinates) {
      alert('Location required to activate exclusive')
      return
    }

    // Capture activation click (both original and new format)
    capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_CLICK, {
      merchant_id: merchant.id,
    })
    capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_CLICKED, {
      merchant_id: merchant.id,
      path: window.location.pathname,
    })

    if (!isMockMode()) {
      // Check location first
      try {
        const locationCheckResult = await checkLocation(coordinates.lat, coordinates.lng)
        if (!locationCheckResult.in_charger_radius) {
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_BLOCKED_OUTSIDE_RADIUS, {
            merchant_id: merchant.id,
            distance_m: locationCheckResult.distance_m,
            required_radius_m: 150,
          })
          alert(`You must be at the charger to activate. Distance: ${locationCheckResult.distance_m?.toFixed(0)}m, required: 150m`)
          return
        }

        // Check confidence tier (from intent data)
        const confidenceTier = intentData?.confidence_tier
        if (confidenceTier && !['A', 'B'].includes(confidenceTier)) {
          alert('Exclusive activation requires high confidence location. Please wait for better GPS signal.')
          return
        }

        // Activate exclusive via backend
        try {
          const response = await activateExclusiveMutation.mutateAsync({
            merchant_id: merchant.id,
            charger_id: locationCheckResult.nearest_charger_id || 'unknown',
            lat: coordinates.lat,
            lng: coordinates.lng,
            accuracy_m: coordinates.accuracy_m,
            intent_session_id: sessionId || undefined,
          })

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

          activateExclusiveLocal(exclusiveMerchant, response.exclusive_session.expires_at)
          chargingState.transitionTo('EXCLUSIVE_ACTIVE')
          setAppChargingState('EXCLUSIVE_ACTIVE')
          
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_SUCCESS, {
            merchant_id: merchant.id,
            exclusive_id: response.exclusive_session.id,
            session_id: response.exclusive_session.id,
          })
        } catch (error: any) {
          console.error('Failed to activate exclusive:', error)
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_FAIL, {
            merchant_id: merchant.id,
            error: error.message || 'Unknown error',
          })
          if (error.status === 403) {
            alert(error.message || 'You must be at the charger to activate exclusive')
          } else {
            alert('Failed to activate exclusive. Please try again.')
          }
          return
        }
      } catch (error) {
        console.error('Location check failed:', error)
        alert('Failed to verify location. Please try again.')
        return
      }
    } else {
      // Mock mode - use local activation
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
      activateExclusiveLocal(exclusiveMerchant)
      chargingState.transitionTo('EXCLUSIVE_ACTIVE')
      setAppChargingState('EXCLUSIVE_ACTIVE')
    }

    setShowActivateModal(false)
    setSelectedMerchant(null)
  }

  const handleOTPSuccess = () => {
    // User successfully authenticated (tokens stored in auth.ts)
    setIsAuthenticated(true)
    setShowActivateModal(false)

    // Proceed to activation if merchant is selected
    if (selectedMerchant) {
      handleActivateExclusiveDirect(selectedMerchant)
    }
  }

  const handleOTPClose = () => {
    setShowActivateModal(false)
  }

  const handleArrived = () => {
    setShowArrivalModal(true)
  }

  const handleArrivalDone = () => {
    setShowArrivalModal(false)
    setShowCompletionModal(true)
  }

  const handleCompletionContinue = async () => {
    setShowCompletionModal(false)
    
    // Capture completion click (both original and new format)
    if (activeExclusive) {
      capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_CLICK, {
        merchant_id: activeExclusive.id,
      })
      capture(DRIVER_EVENTS.EXCLUSIVE_DONE_CLICKED, {
        merchant_id: activeExclusive.id,
        path: window.location.pathname,
      })
    }
    
    // Complete exclusive session via backend
    if (activeExclusive && !isMockMode()) {
      const activeSessionId = activeExclusiveData?.exclusive_session?.id
      if (activeSessionId) {
        try {
          await completeExclusiveMutation.mutateAsync({
            exclusive_session_id: activeSessionId,
          })
          
          capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_SUCCESS, {
            merchant_id: activeExclusive.id,
            session_id: activeSessionId,
          })
        } catch (error: any) {
          console.error('Failed to complete exclusive:', error)
          capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_FAIL, {
            merchant_id: activeExclusive.id,
            error: error.message || 'Unknown error',
          })
          // Continue anyway - show preferences
        }
      }
    }
    
    // Transition to COMPLETE state and show preferences
    chargingState.transitionTo('COMPLETE')
    setShowPreferencesModal(true)
  }

  const handlePreferencesDone = () => {
    setShowPreferencesModal(false)
    // Reset state and return to discovery
    clearExclusive()
    chargingState.transitionTo(appChargingState === 'CHARGING_ACTIVE' ? 'CHARGING_ACTIVE' : 'PRE_CHARGING')
    setAppChargingState(appChargingState === 'CHARGING_ACTIVE' ? 'CHARGING_ACTIVE' : 'PRE_CHARGING')
  }

  const handlePrevSet = () => {
    setCurrentSetIndex((prev) => (prev === 0 ? merchantSets.length - 1 : prev - 1))
  }

  const handleNextSet = () => {
    setCurrentSetIndex((prev) => (prev === merchantSets.length - 1 ? 0 : prev + 1))
  }

  const handleToggleCharging = () => {
    if (chargingState.state === 'PRE_CHARGING') {
      chargingState.transitionTo('CHARGING_ACTIVE')
      setAppChargingState('CHARGING_ACTIVE')
    } else if (chargingState.state === 'CHARGING_ACTIVE') {
      chargingState.transitionTo('PRE_CHARGING')
      setAppChargingState('PRE_CHARGING')
    }
    setCurrentSetIndex(0)
    setSelectedMerchant(null)
    // Reset exclusive state when switching modes
    if (activeExclusive) {
      clearExclusive()
    }
  }

  // State-based headline and subheadline
  const headline = 'What to do while you charge'
  const subheadline =
    chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE'
      ? 'Curated access, active while charging'
      : 'Personalized access during your charge window'

  // Dev console logging
  useEffect(() => {
    console.group('Nerava Integration')
    console.log('Mock mode:', isMockMode())
    console.log('API base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001')
    console.log('Location permission:', locationPermission)
    console.log('Location fix:', locationFix)
    console.log('Coordinates:', coordinates)
    console.log('App charging state:', appChargingState)
    console.log('Charging state machine:', chargingState.state)
    console.log('Session ID:', sessionId)
    console.log('Intent capture loading:', intentLoading)
    console.log('Intent data:', intentData)
    console.groupEnd()
  }, [locationPermission, locationFix, coordinates, appChargingState, sessionId, intentLoading, intentData])

  // Show location denied screen if location is denied or error (and not skipped/browse mode)
  const showLocationDenied = (locationPermission === 'denied' || locationFix === 'error') && !browseMode && locationPermission !== 'skipped'

  const handleTryAgain = () => {
    requestLocationPermission()
  }

  const handleBrowseChargers = () => {
    setBrowseMode(true)
  }

  // If location denied and not in browse mode, show recovery screen
  if (showLocationDenied) {
    return (
      <LocationDeniedScreen
        onTryAgain={handleTryAgain}
        onBrowseChargers={handleBrowseChargers}
      />
    )
  }

  // If exclusive is active, show exclusive view (ignore other states)
  if (activeExclusive && (activeExclusive || chargingState.state === 'EXCLUSIVE_ACTIVE')) {
    return (
      <>
        <ExclusiveActiveView
          merchant={activeExclusive}
          remainingMinutes={remainingMinutes}
          onArrived={handleArrived}
          onToggleLike={handleToggleLike}
          onShare={() => {
            // Share functionality
            const url = `https://nerava.com/merchant/${activeExclusive.id}`
            navigator.clipboard.writeText(url)
          }}
          isLiked={likedMerchants.has(activeExclusive.id)}
        />
        <ArrivalConfirmationModal
          isOpen={showArrivalModal}
          merchantName={activeExclusive.name}
          merchantId={activeExclusive.id}
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

  // Discovery View - Hidden when exclusive is active
  return (
    <>
      <StateTransitionToast
        show={showTransitionToast}
        onHide={() => setShowTransitionToast(false)}
      />
      <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex flex-col h-screen overflow-hidden transition-opacity duration-300">
        {/* Status Header */}
        <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0">
          <div className="flex items-center justify-between px-5 py-3">
            <div className="flex items-center gap-1.5">
              <span className="tracking-tight text-[#050505]">NERAVA</span>
              <Zap className="w-4 h-4 fill-[#1877F2] text-[#1877F2]" />
              {useDemoData && (
                <Badge variant="default" className="ml-2">
                  Demo Mode
                </Badge>
              )}
              {browseMode && (
                <Badge variant="default" className="ml-2">
                  Browse mode
                </Badge>
              )}
            </div>
            <button
              onClick={handleToggleCharging}
              className="px-3 py-1.5 bg-[#1877F2] rounded-full hover:bg-[#166FE5] active:scale-95 transition-all flex items-center justify-center"
            >
              <span className="text-xs text-white leading-none">
                {chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE' ? 'Charging Active' : 'Pre-Charging'}
              </span>
            </button>
          </div>
        </header>

        {/* Moment Header */}
        <div className="text-center px-6 pt-4 pb-1 flex-shrink-0">
          <h1 className="text-2xl sm:text-3xl mb-1 whitespace-nowrap">{headline}</h1>
          <p className="text-sm text-[#65676B] whitespace-nowrap">{subheadline}</p>
        </div>

        {/* Merchant Carousel */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* Show error banner if API failed and not in demo mode */}
          {hasApiError && !useDemoData && !useMockData && (
            <ErrorBanner
              message="We couldn't load chargers right now. Retry."
              onRetry={() => refetchIntent()}
              isLoading={intentLoading}
            />
          )}
          
          {intentLoading && !useMockData && locationFix === 'locating' ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-[#65676B]">Finding nearby experiences...</p>
              </div>
            </div>
          ) : activeSets.length === 0 && !useMockData && !hasApiError ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-[#65676B]">No nearby experiences found yet.</p>
              </div>
            </div>
          ) : activeSets.length > 0 ? (
            <MerchantCarousel
              merchantSet={currentSet}
              isCharging={chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE'}
              onPrevSet={handlePrevSet}
              onNextSet={handleNextSet}
              currentSetIndex={currentSetIndex}
              totalSets={activeSets.length}
              onMerchantClick={handleMerchantClick}
              likedMerchants={likedMerchants}
            />
          ) : null}
        </div>
      </div>

      {/* Merchant Details Modal */}
      {selectedMerchant && (
        <MerchantDetailModal
          merchant={selectedMerchant}
          isCharging={chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE'}
          isInChargerRadius={isInChargerRadius}
          onClose={handleCloseMerchantDetails}
          onToggleLike={handleToggleLike}
          onActivateExclusive={handleActivateExclusive}
          likedMerchants={likedMerchants}
        />
      )}

      {/* Activation Modal (OTP) */}
      <ActivateExclusiveModal
        isOpen={showActivateModal}
        onClose={handleOTPClose}
        onSuccess={handleOTPSuccess}
      />

      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={showPreferencesModal}
        onClose={handlePreferencesDone}
      />

      {/* Analytics Debug Panel (dev only) */}
      <AnalyticsDebugPanel />
    </>
  )
}

